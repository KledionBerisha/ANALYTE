"""
Testet e katalogut normativ.

"""

import ast
from pathlib import Path

import pytest

from analyte.domain.enums import ViolationType
from analyte.domain.policy import (
    MAX_GENERATION_ATTEMPTS,
    POLICY_VERSION,
    PROHIBITIVE_POLICIES,
    RULE_BY_ID,
    RULE_BY_VIOLATION,
    RULE_CATALOG,
    RULES_VERSION,
    SafetyPolicy,
    sentence_local_violations,
)

DOMAIN_DIR = Path(__file__).resolve().parents[2] / "backend" / "src" / "analyte" / "domain"


# Plotësia e katalogut


def test_every_violation_type_has_a_rule():
    """Një lloj shkeljeje pa rregull do të thotë defekt që asnjë komponent
    nuk e zbulon dot — dhe kolonë bosh në Tabelën 13."""
    assert set(RULE_BY_VIOLATION) == set(ViolationType)


def test_rule_ids_are_unique():
    assert len(RULE_BY_ID) == len(RULE_CATALOG)


def test_rule_branch_matches_violation_branch():
    """Dega e deklaruar në katalog dhe ajo e nxjerrë nga enum-i duhet të
    jenë e njëjta gjë; ndryshe ndarja A/B e rezultateve bëhet e pabesueshme."""
    for rule in RULE_CATALOG:
        assert rule.branch == rule.violation.branch, rule.id


def test_branch_a_rules_are_the_four_exact_ones():
    branch_a = {r.id for r in RULE_CATALOG if r.branch == "A"}
    assert branch_a == {"R1", "R2", "R3", "R4"}


def test_context_dependent_rules_are_the_coverage_rules():
    """Vetëm mungesat kërkojnë pamje mbi tërë daljen: gjetja kritike e
    palakuar (R4) dhe rekomandimi i hequr (R8)."""
    assert {r.id for r in RULE_CATALOG if r.requires_context} == {"R4", "R8"}


def test_sentence_local_violations_exclude_coverage_rules():
    local = sentence_local_violations()
    assert ViolationType.MISSING_CRITICAL not in local
    assert ViolationType.OMITTED_RECOMMENDATION not in local
    assert ViolationType.POLARITY_FLIP in local
    assert len(local) == len(ViolationType) - 2


def test_versions_are_recorded():
    assert RULES_VERSION and POLICY_VERSION
    assert MAX_GENERATION_ATTEMPTS == 2


# Politika e sigurisë


def test_all_eight_policies_exist_with_text():
    assert len(SafetyPolicy) == 8
    for policy in SafetyPolicy:
        assert policy.description_sq.strip()


def test_only_sp1_to_sp3_are_enforced_on_text():
    """SP4-SP8 zbatohen strukturalisht; nëse dikush i shton këtu, do të
    kërkohej shqyrtim teksti për to, çka nuk është plan."""
    assert {p.value for p in PROHIBITIVE_POLICIES} == {"SP1", "SP2", "SP3"}
    assert SafetyPolicy.CRITICAL_ESCALATION.is_prohibition is False
    assert SafetyPolicy.NO_DIAGNOSIS.is_prohibition is True


def test_prohibited_claim_rule_covers_sp1_to_sp3():
    rule = RULE_BY_VIOLATION[ViolationType.PROHIBITED_CLAIM]
    assert rule.id == "SP1-3"


# Pastërtia e paketës domain/


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:  # import relativ brenda domain/
                continue
            if node.module:
                names.add(node.module)
    return names


ALLOWED_TOP_LEVEL = {
    "enum",
    "typing",
    "datetime",
    "decimal",
    "uuid",
    "pydantic",
    "__future__",
    "dataclasses",  # `processing.py` (Attempt, Explanation, Transition): dataclasa të ngrira, jo modele pydantic
}


@pytest.mark.parametrize("module_path", sorted(DOMAIN_DIR.glob("*.py")), ids=lambda p: p.name)
def test_domain_imports_nothing_from_the_rest_of_the_system(module_path):
    """Konventa e §3 e specifikimit, e zbatuar me kod.

    Domeni mban kontratën e të dhënave. Sapo ai të importojë shtresën e
    persistencës ose të gjenerimit, kontrata fillon të varet nga ato dhe
    ndryshimi i tyre e prish atë në heshtje.
    """
    for name in _imported_modules(module_path):
        root = name.split(".")[0]
        assert root != "analyte", f"{module_path.name} importon {name}"
        assert root in ALLOWED_TOP_LEVEL, f"{module_path.name} importon {name}"
