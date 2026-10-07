"""
Trajnimi i klasifikuesit të fjalive (Faza 7) — ekzekutohet në Colab.

    python train_classifier.py --data classifier_data --input sentence --out runs/sentence
    python train_classifier.py --data classifier_data --input context  --out runs/context

"""

from __future__ import annotations

import argparse
import json
import platform
import random
import time
from pathlib import Path

import numpy as np
import torch
import transformers
from sklearn.metrics import f1_score
from torch.utils.data import Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    set_seed,
)

DEFAULT_LENGTH = {"sentence": 128, "context": 384}


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


class Sentences(Dataset):
    """Fjalitë e etiketuara, të tokenizuara një herë."""

    def __init__(self, rows, tokenizer, labels, mode, max_length):
        first = [row["sentence"] for row in rows]
        second = [row["context"] for row in rows] if mode == "context" else None
        self.encodings = tokenizer(
            first,
            second,
            truncation="only_second" if second else True,
            max_length=max_length,
        )
        index = {label: i for i, label in enumerate(labels)}
        self.targets = [index[row["label"]] for row in rows]

    def __len__(self):
        return len(self.targets)

    def __getitem__(self, i):
        item = {key: values[i] for key, values in self.encodings.items()}
        item["labels"] = self.targets[i]
        return item


def macro_f1_without_clean(labels):
    """Macro F1 mbi llojet e defekteve, si metrika e E10.

    `clean` nuk hyn në mesatare: një klasifikues që thotë gjithmonë
    "pastër" do të merrte notë të mirë vetëm prej saj.
    """
    defects = [i for i, label in enumerate(labels) if label != "clean"]

    def compute(prediction):
        predicted = prediction.predictions.argmax(-1)
        return {
            "macro_f1": f1_score(
                prediction.label_ids, predicted, labels=defects, average="macro", zero_division=0
            )
        }

    return compute


@torch.no_grad()
def predict_texts(model, tokenizer, rows, mode, max_length, device, batch=64):
    """Probabilitetet për çdo fjali të çdo teksti."""
    model.eval()
    out = []
    for row in rows:
        sentences = row["sentences"]
        probabilities = []
        for start in range(0, len(sentences), batch):
            chunk = sentences[start : start + batch]
            second = [row["context"]] * len(chunk) if mode == "context" else None
            encoded = tokenizer(
                chunk,
                second,
                truncation="only_second" if second else True,
                max_length=max_length,
                padding=True,
                return_tensors="pt",
            ).to(device)
            logits = model(**encoded).logits
            probabilities += torch.softmax(logits, dim=-1).cpu().tolist()
        out.append(
            {
                "document_id": row["document_id"],
                "label": row["label"],
                "sentences": sentences,
                "probabilities": [[round(p, 6) for p in ps] for ps in probabilities],
            }
        )
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="train_classifier")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--input", choices=("sentence", "context"), default="sentence")
    parser.add_argument("--model", default="xlm-roberta-base")
    parser.add_argument("--epochs", type=float, default=3)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--limit", type=int, default=None, help="vetëm për prova të shpejta")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    set_seed(args.seed)
    random.seed(args.seed)
    max_length = args.max_length or DEFAULT_LENGTH[args.input]
    labels = json.loads((args.data / "labels.json").read_text(encoding="utf-8"))

    train_rows = read_jsonl(args.data / "train.jsonl")
    val_rows = read_jsonl(args.data / "val.jsonl")
    val_texts = read_jsonl(args.data / "val_texts.jsonl")
    test_texts = read_jsonl(args.data / "test_texts.jsonl")
    if args.limit:
        train_rows, val_rows = train_rows[: args.limit], val_rows[: args.limit // 4]
        val_texts, test_texts = val_texts[: args.limit // 20], test_texts[: args.limit // 20]

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model,
        num_labels=len(labels),
        id2label=dict(enumerate(labels)),
        label2id={label: i for i, label in enumerate(labels)},
        # Koka e klasifikimit krijohet e re për etiketat tona; nëse modeli
        # nisës ka një kokë tjetër, ajo zëvendësohet në vend që të ndalet.
        ignore_mismatched_sizes=True,
    )

    train = Sentences(train_rows, tokenizer, labels, args.input, max_length)
    val = Sentences(val_rows, tokenizer, labels, args.input, max_length)

    # transformers 5 e bashkoi `warmup_ratio` te `warmup_steps` (numër dhjetor
    # = përpjesë); versioni 4 pranon vetëm të parin. Colab-u mund të ketë
    # cilindo, prandaj zgjidhet sipas nënshkrimit.
    import inspect

    if "warmup_ratio" in inspect.signature(TrainingArguments.__init__).parameters:
        warmup = {"warmup_ratio": 0.1}
    else:
        warmup = {"warmup_steps": 0.1}

    training_args = TrainingArguments(
        output_dir=str(args.out / "checkpoints"),
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        per_device_train_batch_size=args.batch,
        per_device_eval_batch_size=args.batch * 2,
        **warmup,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        fp16=torch.cuda.is_available(),
        seed=args.seed,
        report_to=[],
        logging_steps=50,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train,
        eval_dataset=val,
        processing_class=tokenizer,
        compute_metrics=macro_f1_without_clean(labels),
    )

    started = time.time()
    trainer.train()
    best = trainer.evaluate()
    elapsed = time.time() - started

    model_dir = args.out / "model"
    trainer.save_model(str(model_dir))
    tokenizer.save_pretrained(str(model_dir))

    device = trainer.model.device
    for name, rows in (("val", val_texts), ("test", test_texts)):
        predictions = predict_texts(trainer.model, tokenizer, rows, args.input, max_length, device)
        with (args.out / f"predictions_{name}.jsonl").open("w", encoding="utf-8") as handle:
            for row in predictions:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    run = {
        "input": args.input,
        "model": args.model,
        "labels": labels,
        "max_length": max_length,
        "epochs": args.epochs,
        "learning_rate": args.lr,
        "batch": args.batch,
        "seed": args.seed,
        "limit": args.limit,
        "train_sentences": len(train),
        "val_sentences": len(val),
        "val_macro_f1_sentences": best.get("eval_macro_f1"),
        "training_seconds": round(elapsed),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "versions": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "numpy": np.__version__,
        },
        "data_meta": json.loads((args.data / "meta.json").read_text(encoding="utf-8")),
    }
    (args.out / "run.json").write_text(
        json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: run[k] for k in ("input", "val_macro_f1_sentences", "training_seconds")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
