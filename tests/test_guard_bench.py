"""Pytest: Guard-Bench ist deterministisch und vollständig grün.

Diese Datei ist der CI-Bridge — sie lädt `guard/bench_data/guard-bench.json`
und erzwingt: 0 Fehler + alle Cases vorhanden. Jeder neu hinzugefügte Case
muss hier automatisch grün sein, sonst fällt die CI.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from guard.bench import bench_summary, load_bench, run_bench
from guard.core import detect_prompt_injection

BENCH = Path(__file__).resolve().parent.parent / "guard" / "bench_data" / "guard-bench.json"


def test_bench_file_exists() -> None:
    assert BENCH.exists(), f"Guard-Bench fehlt: {BENCH}"


def test_bench_loads_and_has_minimum_size() -> None:
    cases = load_bench()
    # Minimum: 24 Cases (12+12) — jede Kategorie braucht Substanz
    assert len(cases) >= 24, f"Weniger als 24 Cases: {len(cases)}"


def test_bench_ids_unique() -> None:
    cases = load_bench()
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)), f"Nicht eindeutige IDs: {sorted(set(i for i in ids if ids.count(i) > 1))}"


def test_bench_all_cases_have_required_fields() -> None:
    for c in load_bench():
        assert "id" in c, f"Case fehlt 'id': {c}"
        assert "input" in c and isinstance(c["input"], str), f"Case {c.get('id')}: 'input' fehlt oder nicht String"
        assert c.get("expect") in ("block", "pass"), f"Case {c.get('id')}: 'expect' muss 'block'/'pass' sein"
        assert "note" in c, f"Case {c.get('id')}: 'note' fehlt (Begründung)"


def test_bench_is_fully_green() -> None:
    result = run_bench()
    assert result["passed"] == result["total"], (
        f"GUARD-Bench nicht grün:\n{bench_summary(result)}"
    )


def test_bench_detects_injection_category() -> None:
    # Mindestens ein 'inj' Case, der als 'block' erwartet wird
    inj_block = [c for c in load_bench() if c["id"].startswith("inj-") and c["expect"] == "block"]
    assert inj_block, "Kein inj-Case mit expect=block — die Bench wäre ein Leerfleck"
    for c in inj_block:
        assert detect_prompt_injection(c["input"]) is True


def test_bench_has_documented_false_negatives() -> None:
    # Mindestens ein dokumentiertes False-Negative — das ist die Ehrlichkeitsprüfung
    fn = [c for c in load_bench() if c["id"].startswith("adv-") and c["expect"] == "pass"]
    assert fn, "Kein dokumentiertes False-Negative (adv-Cases mit expect=pass) — die Grenzen werden nicht offengelegt"


def test_bench_summary_format() -> None:
    result = run_bench()
    summary = bench_summary(result)
    assert "GUARD-BENCH" in summary
    assert "/3" in summary or "/4" in summary  # z.B. 30/32, 12/12 — 2-stellige Zahl im Denominator
