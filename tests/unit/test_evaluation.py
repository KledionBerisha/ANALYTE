"""
Testet e infrastrukturës së vlerësimit.

Një harness i prishur nuk dështon: ai prodhon numra. Prandaj testet këtu
mbështeten te dy kufij të njohur paraprakisht.

  - **Orakulli** — sistemi që kthen vetë të vërtetën — duhet të arrijë
    vlerën e përsosur. Një metrikë që nuk e arrin dot atë është e prishur
    në vetvete, dhe pa këtë kontroll gabimi i saj do të dukej më vonë si
    dobësi e sistemit të matur.
  - **Sistemi bosh** — ai që nuk nxjerr asgjë — nuk duhet të marrë kurrë
    notë të mirë. Metrika që e shpërblen heshtjen është më e keqe se
    asnjë metrikë.
"""

from dataclasses import fields
from decimal import Decimal
from uuid import uuid4

import pytest

from analyte.domain.enums import (
    AnalyteStatus,
    DetectedBy,
    ProcessingState,
    ReferenceSource,
    ViolationType,
)
from analyte.domain.models import (
    AnalyteFinding,
    GroundingContext,
    VerificationResult,
    Violation,
)
from data_generator.generate import build_corpus, write_corpus
from evaluation import dataset as dataset_module
from evaluation import experiments as registry
from evaluation import harness
from evaluation.metrics import classification, crossref, detector, extraction, prose, violations
from evaluation.metrics.base import PRF, ConfusionMatrix, count_sentences, micro_average
from evaluation.metrics.detector import CLEAN, Judgement
from evaluation.pipeline import DocumentInput, EmptyPipeline, OraclePipeline, PipelineOutput

CORPUS_SEED = 21
CORPUS_SIZE = 6


@pytest.fixture(scope="module")
def corpus_dir(tmp_path_factory):
    directory = tmp_path_factory.mktemp("corpus")
    write_corpus(build_corpus(CORPUS_SEED, CORPUS_SIZE), CORPUS_SEED, directory)
    return directory


@pytest.fixture(scope="module")
def data(corpus_dir):
    return dataset_module.load(corpus_dir)


# --------------------------------------------------------------------
# Bazat e metrikave
# --------------------------------------------------------------------


def test_prf_arithmetic():
    counts = PRF(true_positive=8, false_positive=2, false_negative=4)
    assert counts.precision == 0.8
    assert counts.recall == pytest.approx(2 / 3)
    assert counts.f1 == pytest.approx(0.7272727, rel=1e-5)
    assert counts.support == 12


def test_prf_returns_none_instead_of_zero_when_nothing_was_measured():
    """Zeroja është pohim; None thotë se nuk kishte çfarë të matej."""
    assert PRF(0, 0, 0).precision is None
    assert PRF(0, 0, 0).recall is None
    assert PRF(0, 0, 0).f1 is None
    assert PRF(0, 0, 5).precision is None  # asgjë e parashikuar
    assert PRF(0, 0, 5).recall == 0.0  # por kishte çfarë të gjendej


def test_prf_addition_merges_counts():
    assert micro_average({"a": PRF(1, 2, 3), "b": PRF(4, 5, 6)}) == PRF(5, 7, 9)


def test_confusion_matrix_per_class():
    matrix = ConfusionMatrix()
    matrix.add("high", "high")
    matrix.add("high", "normal")
    matrix.add("normal", "normal")
    assert matrix.accuracy == pytest.approx(2 / 3)
    per_class = matrix.per_class()
    assert per_class["high"] == PRF(1, 0, 1)
    assert per_class["normal"] == PRF(1, 1, 0)


@pytest.mark.parametrize(
    "text,expected",
    [("", 0), ("Një fjali.", 1), ("Një. Dy. Tre.", 3), ("Pa pikë fare", 1)],
)
def test_sentence_counting(text, expected):
    assert count_sentences(text) == expected


# --------------------------------------------------------------------
# Kufijtë: orakulli dhe sistemi bosh
# --------------------------------------------------------------------


def _contexts(data):
    return [(case.truth, case.truth) for case in data.cases]


def _empty_contexts(data):
    return [
        (case.truth, GroundingContext(document_id=case.document_id)) for case in data.cases
    ]


def test_extraction_is_perfect_on_the_oracle(data):
    result = extraction.measure(_contexts(data))
    assert result["micro"]["f1"] == 1.0
    for field in extraction.FIELDS:
        assert result["per_field"][field]["f1"] == 1.0


def test_extraction_gives_no_credit_for_silence(data):
    result = extraction.measure(_empty_contexts(data))
    assert result["micro"]["recall"] == 0.0
    assert result["micro"]["f1"] is None  # saktësia e papërkufizuar
    assert result["per_field"]["analyte"]["fn"] > 0


def test_missing_row_costs_every_field_not_just_the_analyte(data):
    """Një rresht i humbur nuk është neutral për fushat e tij; përndryshe
    një sistem që nxjerr vetëm rreshtat e lehtë do të dukej i përsosur."""
    truth = data.cases[0].truth
    partial = truth.model_copy(update={"findings": truth.findings[:1]})
    result = extraction.measure([(truth, partial)])
    missing = len(truth.findings) - 1
    assert result["per_field"]["value"]["fn"] == missing
    assert result["per_field"]["unit"]["fn"] == missing


def test_wrong_value_counts_on_both_sides(data):
    truth = data.cases[0].truth
    broken = truth.findings[0].model_copy(update={"value_canonical": Decimal("99999")})
    predicted = truth.model_copy(update={"findings": (broken, *truth.findings[1:])})
    result = extraction.measure([(truth, predicted)])
    assert result["per_field"]["value"]["fp"] == 1
    assert result["per_field"]["value"]["fn"] == 1
    assert result["per_field"]["analyte"]["f1"] == 1.0  # analiti u gjet; vlera jo


def test_classification_is_perfect_on_the_oracle(data):
    result = classification.measure(_contexts(data))
    assert result["overall"]["accuracy"] == 1.0
    assert result["unmatched_findings"] == 0


def test_classification_does_not_double_count_missing_rows(data):
    result = classification.measure(_empty_contexts(data))
    assert result["overall"]["total"] == 0
    assert result["unmatched_findings"] > 0


def _uninterpretable_context() -> GroundingContext:
    """Një dokument me një vlerë të vetme pa interval referent.

    Ndërtohet dhe nuk kërkohet te korpusi: rastet e SP5 janë të rralla
    atje, dhe një test që kapërcehet kur fati nuk e sjell rastin nuk mat
    asgjë — pikërisht ashtu si metrika që ai mbron.
    """
    finding = AnalyteFinding(
        analyte_code="2276-4",
        analyte_name_raw="Ferritina",
        analyte_name_canonical="Ferritinë në serum",
        value_raw="212",
        value=Decimal("212"),
        unit_raw="ng/mL",
        unit_canonical="ng/mL",
        value_canonical=Decimal("212"),
        ref_source=ReferenceSource.NONE,
        status=AnalyteStatus.UNINTERPRETABLE,
        page=1,
    )
    return GroundingContext(document_id=uuid4(), findings=(finding,))


def test_uninterpretable_recall_is_reported_separately():
    """SP5 si numër. Rastet janë të pakta, prandaj saktësia e
    përgjithshme do t'i fshihte plotësisht."""
    truth = _uninterpretable_context()
    assert classification.measure([(truth, truth)])["uninterpretable_recall"] == 1.0


def test_guessing_a_status_without_an_interval_is_visible():
    """Hamendësimi i një statusi aty ku nuk ka interval është shkelje e
    SP5. Saktësia e përgjithshme mbi një dokument të vetëm do ta shihte
    si një gabim si çdo tjetër; kjo metrikë e veçon."""
    truth = _uninterpretable_context()
    guessed = truth.findings[0].model_copy(
        update={
            "ref_low": Decimal("30"),
            "ref_high": Decimal("400"),
            "ref_source": ReferenceSource.INTERNAL_TABLE,
            "status": AnalyteStatus.NORMAL,
        }
    )
    predicted = truth.model_copy(update={"findings": (guessed,)})
    result = classification.measure([(truth, predicted)])
    assert result["uninterpretable_recall"] == 0.0


def test_crossref_is_perfect_on_the_oracle(data):
    assert crossref.measure(_contexts(data))["overall"]["accuracy"] == 1.0


def test_crossref_marks_silence_as_missing(data):
    result = crossref.measure(_empty_contexts(data))
    assert result["overall"]["accuracy"] == 0.0
    matrix = result["overall"]["matrix"]
    assert any(key.endswith(f"->{crossref.MISSING}") for key in matrix)


# --------------------------------------------------------------------
# PK3 dhe PK5 — varen nga dalja e gjeneruar
# --------------------------------------------------------------------


def _output(explanation="", violations_=(), state=ProcessingState.DELIVERED, context=None):
    return PipelineOutput(
        context=context or GroundingContext(document_id=uuid4()),
        explanation=explanation,
        verification=(
            VerificationResult(
                explanation_id=uuid4(),
                rules_version="r1.0",
                duration_ms=1,
                violations=tuple(violations_),
            )
            if explanation
            else None
        ),
        state=state,
    )


def _violation(kind: ViolationType) -> Violation:
    return Violation(
        type=kind,
        detected_by=DetectedBy.RULE,
        sentence="fjali",
        evidence="dëshmi",
    )


def test_prose_reports_nothing_when_nothing_was_generated(data):
    """Rregresioni: pa dalje, ruajtja e mohimit nuk është 1.0 por e pamatur.

    Sistemi bosh nuk përmbys asnjë mohim sepse nuk shkruan asnjë fjali;
    kjo nuk është besnikëri.
    """
    result = prose.measure([(case.truth, _output()) for case in data.cases])
    assert result["negation_preservation"] is None
    assert result["hedge_preservation"] is None
    assert result["documents_with_output"] == 0


def test_prose_counts_a_flip_against_preservation(data):
    truth = next(
        case.truth
        for case in data.cases
        if any(a.polarity.value == "negated" for a in case.truth.assertions)
    )
    negated = sum(1 for a in truth.assertions if a.polarity.value == "negated")
    result = prose.measure(
        [(truth, _output("Një fjali. Dy fjali.", [_violation(ViolationType.POLARITY_FLIP)]))]
    )
    assert result["negation_preservation"] == pytest.approx((negated - 1) / negated)
    assert result["counts"]["polarity_flips"] == 1


def test_violations_separate_produced_from_reaching_the_user(data):
    """Thelbi i ablacionit: verifikimi nuk e bën modelin më të mirë, ai
    vendos çfarë del jashtë. Nëse të dy numrat raportohen si një, E8 dhe
    E9 nuk kanë çfarë të tregojnë."""
    truth = data.cases[0].truth
    delivered = _output("Një. Dy.", [_violation(ViolationType.UNGROUNDED_NUMBER)])
    blocked = _output(
        "Një. Dy.",
        [_violation(ViolationType.UNGROUNDED_NUMBER)],
        state=ProcessingState.TEMPLATE_FALLBACK,
    )
    result = violations.measure([(truth, delivered), (truth, blocked)])
    assert result["violations_produced"] == 2
    assert result["violations_reaching_user"] == 1
    assert result["template_fallbacks"] == 1
    assert result["rate_produced_per_100_sentences"] == 50.0


def test_violations_rate_is_none_without_sentences(data):
    result = violations.measure([(case.truth, _output()) for case in data.cases])
    assert result["rate_produced_per_100_sentences"] is None
    assert result["violations_produced"] == 0


# --------------------------------------------------------------------
# PK6 — zbuluesit
# --------------------------------------------------------------------


def test_detector_scores_per_defect_type():
    judgements = [
        Judgement(ViolationType.UNGROUNDED_NUMBER, ViolationType.UNGROUNDED_NUMBER),
        Judgement(ViolationType.UNGROUNDED_NUMBER, None),
        Judgement(ViolationType.POLARITY_FLIP, ViolationType.HEDGE_REMOVED),
        Judgement(None, None),
        Judgement(None, ViolationType.UNGROUNDED_NUMBER),
    ]
    result = detector.measure(judgements)
    numbers = result["per_defect_type"][ViolationType.UNGROUNDED_NUMBER.value]
    assert numbers["tp"] == 1 and numbers["fn"] == 1 and numbers["fp"] == 1
    assert result["false_alarms_on_clean"] == 1
    assert CLEAN not in result["per_defect_type"]
    assert result["samples"] == 5


def test_detector_is_perfect_when_every_label_matches():
    judgements = [
        Judgement(ViolationType.HEDGE_REMOVED, ViolationType.HEDGE_REMOVED),
        Judgement(None, None),
    ]
    result = detector.measure(judgements)
    assert result["macro_f1"] == 1.0
    assert result["false_alarms_on_clean"] == 0


# --------------------------------------------------------------------
# Korpusi dhe kufiri me sistemin
# --------------------------------------------------------------------


def test_dataset_loads_with_identity(data):
    assert len(data) == CORPUS_SIZE
    assert data.seed == CORPUS_SEED
    assert data.version.startswith("gen-")
    assert all(case.truth.findings for case in data.cases)


def test_dataset_version_changes_with_the_resource_tables(data):
    altered = dict(data.manifest)
    altered["resources"] = dict(altered["resources"])
    altered["resources"]["analytes.csv"] = "0" * 64
    assert dataset_module.dataset_version(altered) != data.version


def test_channel_filter_splits_the_corpus(data):
    digital = data.filter(channel="digital")
    scanned = data.filter(channel="scanned")
    assert len(digital) + len(scanned) == len(data)
    assert all(not case.is_scanned for case in digital.cases)


def test_document_input_carries_no_ground_truth():
    """Kufiri i vlefshmërisë, i zbatuar me kod.

    Nëse e vërteta bazë do të kalonte nëpër këtu, çdo numër i harness-it
    do të ishte i pambrojtshëm — dhe asgjë nuk do ta tregonte.
    """
    assert {f.name for f in fields(DocumentInput)} == {"document_id", "pdf_path"}


def test_pipeline_only_ever_sees_document_input(data):
    seen = []

    class Spy:
        name, version = "spy", "0"

        def run(self, document):
            seen.append(document)
            return PipelineOutput(context=GroundingContext(document_id=document.document_id))

    harness.run_experiment(registry.get("E3"), data, Spy())
    assert seen and all(isinstance(item, DocumentInput) for item in seen)


# --------------------------------------------------------------------
# Harness-i
# --------------------------------------------------------------------


def test_every_experiment_of_the_matrix_is_registered():
    assert [e.id for e in registry.EXPERIMENTS] == [f"E{n}" for n in range(1, 16)]
    for experiment in registry.EXPERIMENTS:
        assert experiment.runnable or experiment.pending_reason


def test_pending_experiments_are_not_silently_zero(data):
    result = harness.run_experiment(registry.get("E10"), data, EmptyPipeline())
    assert not result.measured
    assert result.headline() == harness.NOT_MEASURED
    assert result.metadata["dataset"]["version"] == data.version


def test_result_records_its_provenance(data):
    result = harness.run_experiment(registry.get("E3"), data, EmptyPipeline())
    code = result.metadata["code"]
    assert code["git_sha"] and code["rules_version"]
    assert isinstance(code["working_tree_dirty"], (bool, type(None)))
    assert result.metadata["dataset"]["seed"] == CORPUS_SEED


def test_oracle_reaches_the_perfect_score_through_the_harness(data):
    pipeline = OraclePipeline(truth=data.truth_by_id())
    for experiment_id in ("E1", "E2", "E3", "E5"):
        result = harness.run_experiment(registry.get(experiment_id), data, pipeline)
        assert result.headline().startswith("1.000"), (experiment_id, result.headline())


def test_full_run_writes_a_complete_table(data, tmp_path):
    """Përkufizimi i përfundimit të Fazës 3."""
    results = [
        harness.run_experiment(experiment, data, EmptyPipeline())
        for experiment in registry.EXPERIMENTS
    ]
    for result in results:
        harness.write_result(result, tmp_path)
    summary = harness.write_summary(results, tmp_path)

    text = summary.read_text(encoding="utf-8")
    assert harness.NOT_MEASURED in text
    for experiment in registry.EXPERIMENTS:
        assert f"| {experiment.id} |" in text
        assert (tmp_path / experiment.id / "result.json").exists()
        assert (tmp_path / experiment.id / "table.md").exists()


def test_channel_experiments_report_their_channel(data):
    digital = harness.run_experiment(registry.get("E1"), data, EmptyPipeline())
    scanned = harness.run_experiment(registry.get("E2"), data, EmptyPipeline())
    assert digital.metadata["dataset"]["channel"] == "digital"
    assert scanned.metadata["dataset"]["channel"] == "scanned"
    assert digital.metadata["dataset"]["documents"] != len(data) or len(data) == 0


# --------------------------------------------------------------------
# Gjenerimi përmes harness-it (E7, E8)
# --------------------------------------------------------------------
#
# Shablloni është për gjenerimin ajo që orakulli është për nxjerrjen: mbi
# të, çdo metrikë e gjenerimit duhet të dalë e përsosur. Gjeneruesit e
# skriptuar japin pastaj rastet që shablloni nuk i jep dot — defekte në
# përpjekjen e parë, dështime të dyfishta.


class _Scripted:
    """Një hap për çdo thirrje, i përsëritur për çdo dokument."""

    name = "scripted"

    def __init__(self, *steps):
        self.steps = steps
        self.calls = 0

    def __call__(self, context, feedback):
        from analyte.generation.templates import build

        step = self.steps[self.calls % len(self.steps)]
        self.calls += 1
        text = build(context)
        return text if step == "clean" else f"{text} Vlera e matur është 987654."


def _run(data, experiment_id, pipeline):
    return harness.run_experiment(registry.get(experiment_id), data, pipeline)


def test_template_generation_is_perfect_through_the_harness(data):
    from analyte.generation.templates import TemplateGenerator
    from evaluation.pipeline import GenerationPipeline

    result = _run(data, "E8", GenerationPipeline(TemplateGenerator(), ablation="E8"))
    metrics = result.metrics
    assert metrics["documents_with_output"] > 0
    assert metrics["violations_produced"] == 0
    assert metrics["violations_reaching_user"] == 0
    assert metrics["template_fallbacks"] == 0
    assert metrics["clean_deliveries"] == metrics["documents_with_output"]


def test_rejected_first_draft_counts_as_produced_but_not_delivered(data):
    """E8 — përpjekja e parë me defekt, e dyta e pastër."""
    from evaluation.pipeline import GenerationPipeline

    pipeline = GenerationPipeline(_Scripted("defect", "clean"), ablation="E8")
    metrics = _run(data, "E8", pipeline).metrics
    documents = metrics["documents_with_output"]

    assert metrics["violations_produced"] == documents
    assert metrics["violations_reaching_user"] == 0
    assert metrics["template_fallbacks"] == 0


def test_double_failure_reaches_the_template_not_the_user(data):
    from evaluation.pipeline import GenerationPipeline

    pipeline = GenerationPipeline(_Scripted("defect"), ablation="E8")
    metrics = _run(data, "E8", pipeline).metrics
    documents = metrics["documents_with_output"]

    assert metrics["violations_produced"] == 2 * documents
    assert metrics["violations_reaching_user"] == 0
    assert metrics["template_fallbacks"] == documents


def test_without_verification_every_violation_reaches_the_user(data):
    """E7 — pa verifikim, të prodhuarat dhe ato te përdoruesi janë një."""
    from evaluation.pipeline import GenerationPipeline

    pipeline = GenerationPipeline(_Scripted("defect"), ablation="E7")
    metrics = _run(data, "E7", pipeline).metrics
    assert metrics["violations_produced"] == metrics["documents_with_output"] > 0
    assert metrics["violations_reaching_user"] == metrics["violations_produced"]
    assert metrics["template_fallbacks"] == 0


def test_an_ablation_is_never_filed_under_another_condition(data):
    """Një ekzekutim i vetëm nuk mbush E6-E9 me të njëjtat numra."""
    from analyte.generation.templates import TemplateGenerator
    from evaluation.pipeline import GenerationPipeline

    e8 = GenerationPipeline(TemplateGenerator(), ablation="E8")
    for experiment_id in ("E6", "E7", "E9"):
        result = _run(data, experiment_id, e8)
        assert not result.measured, experiment_id
        assert "E8" in result.reason

    silent = _run(data, "E8", EmptyPipeline())
    assert not silent.measured
    assert "nuk gjeneron" in silent.reason


def test_conditions_the_pipeline_cannot_implement_are_refused():
    """E6 kërkon dokumentin e papërpunuar, E9 klasifikuesin."""
    from analyte.generation.templates import TemplateGenerator
    from evaluation.pipeline import GenerationPipeline

    for condition in ("E6", "E9"):
        with pytest.raises(ValueError, match=condition):
            GenerationPipeline(TemplateGenerator(), ablation=condition)
