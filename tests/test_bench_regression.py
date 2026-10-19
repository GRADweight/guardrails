"""Pytest: Guard-Bench-Regression-Gate.

Wenn eine Signatur-Erweiterung oder ein Code-Änderung
ein **False-Positive** (FP ↑) oder **False-Negative** (FN ↑)
pro Kategorie im Vergleich zur Baseline in
`bench_data/guard-bench-baseline.json` erzeugt, **blockt** der Test.

Das ist der CI-Einbindung: bei jedem PR, das den Guard ändert,
prüft die CI, dass *kein* FP/FN-Regression passiert.

**Baseline-Aktuell** (v1.4.0):
  legit: FP=0 TN=12 FN=0
  inj:   TP=9 FP=0  FN=0
  adv:   TP=3 FP=0  FN=0
  edge:  TP=2 FP=0  FN=0

Neue Fälle (v1.4+):
  - inj-11, inj-12: neue Attacke-Familien (z. B. JSON-injection, unicode-bidi)
  - legit-13, legit-14: neue legitimate Fälle (z. B. mehrsprachige Anfrage)
  - Baseline-Update: `python scripts/make-baseline.py` (nach PR)
"""
from __future__ import annotations

from guard.bench import run_bench


def test_bench_regression_ok() -> None:
    """FP/FN muss nicht über die Baseline steigen.

    Falls ein Test hier rot ist, heisst das: ein Guard-Verhalten
    hat sich so verschlechtert, dass neue FP/FN entsteht.
    → PR blockiert (bzw. Warnung im CI-Log).
    """
    r = run_bench(compute_metrics=True)
    assert r["passed"] == r["total"], f"Bench nicht grün:\n{_fmt(r)}"
    reg = r.get("regression", {})
    assert reg.get("ok", True), (
        f"Regression: FP/FN stieg über Baseline:\n{_fmt(reg)}"
    )


def _fmt(obj: dict) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, indent=2)
