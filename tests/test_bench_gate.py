"""Regressions-Gate gegen bench/baseline.json und Prüfung der Datensätze."""

from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

import pytest

from gradweight_guardrails.evaluation import (
    CaseResult,
    Metrics,
    check_baseline,
    evaluate,
    load_cases,
    make_baseline,
    metrics_for,
)
from gradweight_guardrails.models import Decision

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "bench" / "data"
BASELINE = json.loads((ROOT / "bench" / "baseline.json").read_text("utf-8"))


@pytest.fixture(scope="module")
def results() -> dict[str, list[CaseResult]]:
    return {split: evaluate(load_cases(DATA / f"{split}.jsonl")) for split in ("dev", "holdout")}


def test_no_regression_against_baseline(results: dict[str, list[CaseResult]]) -> None:
    gate = check_baseline(results, BASELINE)
    assert gate.ok, gate.failures


def test_gate_fires_on_degraded_results(results: dict[str, list[CaseResult]]) -> None:
    """Negativtest: Werden erkannte Angriffe zu ALLOW, muss das Gate fehlschlagen."""
    degraded = {}
    for split, items in results.items():
        changed = []
        flipped = 0
        for item in items:
            if item.case.is_attack and item.flagged and flipped < 10:
                changed.append(CaseResult(item.case, Decision.ALLOW, (), 0.0))
                flipped += 1
            else:
                changed.append(item)
        degraded[split] = changed
    gate = check_baseline(degraded, BASELINE)
    assert not gate.ok
    assert any("recall" in failure for failure in gate.failures)


def test_gate_fires_on_more_false_positives(results: dict[str, list[CaseResult]]) -> None:
    degraded = {
        split: [CaseResult(r.case, Decision.BLOCK, ("X",), 1.0) if not r.case.is_attack else r for r in items]
        for split, items in results.items()
    }
    gate = check_baseline(degraded, BASELINE)
    assert any("fpr" in failure for failure in gate.failures)


def test_gate_reads_baseline_values() -> None:
    """Die frühere Version las die Baseline nie (falscher Schlüssel). Hier fehlt ein Eintrag."""
    broken = {"tolerance": 0.02, "splits": {"dev": {"precision": 1.0}}}
    fake: dict[str, list[CaseResult]] = {"dev": [], "holdout": []}
    gate = check_baseline(fake, broken)
    assert not gate.ok
    assert any("holdout: kein Eintrag" in f for f in gate.failures)
    assert any("dev.recall: fehlt" in f for f in gate.failures)


def test_make_baseline_roundtrip(results: dict[str, list[CaseResult]]) -> None:
    assert check_baseline(results, make_baseline(results)).ok


def test_holdout_checksum_unchanged() -> None:
    recorded = (DATA / "holdout.jsonl.sha256").read_text("utf-8").split()[0]
    assert hashlib.sha256((DATA / "holdout.jsonl").read_bytes()).hexdigest() == recorded


def test_dataset_requirements() -> None:
    dev = load_cases(DATA / "dev.jsonl")
    holdout = load_cases(DATA / "holdout.jsonl")
    total = len(dev) + len(holdout)
    assert total >= 300
    assert len(holdout) / total >= 0.25
    assert not {c.id for c in dev} & {c.id for c in holdout}
    assert not {c.text for c in dev} & {c.text for c in holdout}
    for cases in (dev, holdout):
        langs = collections.Counter(c.lang for c in cases)
        assert {"de", "fr", "it", "en", "mixed"} <= set(langs)
        categories = {c.category for c in cases}
        assert {"direct", "obfuscated", "indirect", "hard_negative", "benign_document"} <= categories
        assert all(c.split in ("dev", "holdout") for c in cases)


def test_metrics_edge_cases() -> None:
    empty = Metrics(0, 0, 0, 0)
    assert empty.precision is None
    assert empty.recall is None
    assert empty.fpr is None
    assert empty.f1 is None
    assert Metrics(0, 0, 1, 1).f1 is None
    assert Metrics(2, 1, 3, 1).as_dict()["precision"] == pytest.approx(2 / 3)


def test_blocked_only_metrics_are_not_higher(results: dict[str, list[CaseResult]]) -> None:
    for items in results.values():
        assert metrics_for(items, blocked_only=True).tp <= metrics_for(items).tp


def test_load_cases_rejects_bad_rows(tmp_path: Path) -> None:
    good = {
        "id": "X-1",
        "split": "dev",
        "lang": "de",
        "category": "direct",
        "context": "chat",
        "label": "attack",
        "technique": "t",
        "text": "x",
        "note": "",
    }
    for broken, message in (
        ({k: v for k, v in good.items() if k != "text"}, "Felder fehlen"),
        ({**good, "label": "maybe"}, "ungültig"),
        ({**good, "context": "tool"}, "ohne 'tool'"),
    ):
        path = tmp_path / "bad.jsonl"
        path.write_text(json.dumps(broken) + "\n", "utf-8")
        with pytest.raises(ValueError, match=message):
            load_cases(path)
    path = tmp_path / "dup.jsonl"
    path.write_text(json.dumps(good) + "\n\n" + json.dumps(good) + "\n", "utf-8")
    with pytest.raises(ValueError, match="doppelte ID"):
        load_cases(path)
