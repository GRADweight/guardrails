"""Guard-Bench — 4 Kategorien, Metriken per Kategorie, Regression-Gate.

Die Cases in `bench_data/guard-bench.json` sind der objektive Nachweis,
dass der Erstfilter das tut, was er verspricht — und die ehrliche Grenze,
was er NICHT erkennt.

**Neu in v1.4:** Per-Kategorie Metriken (TP/FP/TN/FN) und
`bench_data/guard-bench-baseline.json` als Regression-Base.
Wenn ein Fall sich verschlechtert (FP↑ oder FN↑), blockt der
CI-Regression-Gate-Test.
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter, defaultdict

from .core import detect_prompt_injection

BENCH_FILE = Path(__file__).resolve().parent / "bench_data" / "guard-bench.json"
BASE_FILE = Path(__file__).resolve().parent / "bench_data" / "guard-bench-baseline.json"


def load_bench(path: Path | str | None = None) -> list[dict]:
    """Lädt das Guard-Bench-Korpus. Schema je Case:
        {"id": str, "input": str, "expect": "block"|"pass", "note": str}
    """
    p = Path(path) if path is not None else BENCH_FILE
    with open(p, encoding="utf-8") as fh:
        data = json.load(fh)
    cases = data.get("cases", data) if isinstance(data, dict) else data
    if not isinstance(cases, list):
        raise ValueError("guard-bench.json: 'cases' muss eine Liste sein")
    for c in cases:
        if c.get("expect") not in ("block", "pass"):
            raise ValueError(f"Case {c.get('id')}: expect muss 'block' oder 'pass' sein")
    return cases


def category_of(case_id: str) -> str:
    """Kategorie aus der Case-ID (z. B. `legit-01` → `legit`)."""
    return case_id.split("-", 1)[0] if "-" in case_id else "other"


def run_bench(cases: list[dict] | None = None, compute_metrics: bool = False) -> dict:
    """Führt alle Cases deterministisch durch.

    Rückgabe:
      {
        passed: int,
        failed: [{id, input, expected, got, note}],
        total: int,
        [metrics: {category: {tp, fp, tn, fn}}] (falls compute_metrics=True),
        [regression: {ok: bool, details: [...]}] (falls compute_metrics=True)
      }
    """
    cases = cases if cases is not None else load_bench()
    failed = []
    metrics: dict = defaultdict(lambda: {"tp": 0, "fp": 0, "tn": 0, "fn": 0})
    regression_details = []
    for c in cases:
        got = detect_prompt_injection(c["input"])
        want = c.get("expect") == "block"
        if got is not want:
            failed.append(
                {
                    "id": c.get("id", "?"),
                    "input": c["input"][:70],
                    "expected": "block" if want else "pass",
                    "got": "block" if got else "pass",
                    "note": c.get("note", ""),
                }
            )
        # Metriken
        cat = category_of(c.get("id", "?"))
        m = metrics[cat]
        expected_block = c.get("expect") == "block"
        if expected_block and got:
            m["tp"] += 1
        elif not expected_block and got:
            m["fp"] += 1
        elif expected_block and not got:
            m["fn"] += 1
        else:
            m["tn"] += 1

    result = {"passed": len(cases) - len(failed), "failed": failed, "total": len(cases)}
    if compute_metrics:
        result["metrics"] = dict(metrics)
        # Regression-Gate: Baseline laden, per-Kategorie FP/FN-Fehler melden
        if BASE_FILE.exists():
            with open(BASE_FILE, encoding="utf-8") as f:
                base = json.load(f)
            for cat, m in metrics.items():
                b = base.get(cat, {"fp": 0, "fn": 0})
                if m["fp"] > b.get("fp", 0) or m["fn"] > b.get("fn", 0):
                    regression_details.append({
                        "category": cat,
                        "fp_delta": m["fp"] - b.get("fp", 0),
                        "fn_delta": m["fn"] - b.get("fn", 0),
                        "current": m,
                        "baseline": b,
                    })
            result["regression"] = {"ok": len(regression_details) == 0, "details": regression_details}
        else:
            result["regression"] = {"ok": True, "details": [], "note": "keine Baseline-Datei"}
    return result


def bench_summary(result: dict) -> str:
    """Menschenlesbare Summary (für CI + `python3 -m guard bench`)."""
    if result["failed"]:
        lines = [f"GUARD-BENCH: {result['passed']}/{result['total']} grün"]
        for f in result["failed"]:
            lines.append(
                f"  ROT  {f['id']:8} expected={f['expected']:<5} got={f['got']:<5}  # {f['note']}"
            )
        return "\n".join(lines)
    summary = f"GUARD-BENCH: {result['total']}/{result['total']} grün"
    # Metriken-Extra
    if "metrics" in result:
        lines = [summary, ""]
        for cat, m in sorted(result["metrics"].items()):
            lines.append(f"  {cat:10} TP={m['tp']} FP={m['fp']} TN={m['tn']} FN={m['fn']}")
        # Regression
        if "regression" in result:
            reg = result["regression"]
            if not reg.get("ok", True):
                lines.append("")
                lines.append("  REGRESSION-FAIL:")
                for d in reg["details"]:
                    lines.append(f"    {d['category']}: FP {d['fp_delta']:+d}, FN {d['fn_delta']:+d}")
            else:
                lines.append("  Regression: OK")
        return "\n".join(lines)
    return summary


def format_bench_json(result: dict) -> str:
    """Maschinenlesbares Ergebnis (CI-Log, Machine-Readable)."""
    out = {
        "name": "GRADweight Guard-Bench",
        "passed": result["passed"],
        "failed": result["total"] - result["passed"],
        "total": result["total"],
        "details": result["failed"],
    }
    if "metrics" in result:
        out["metrics"] = result["metrics"]
    if "regression" in result:
        out["regression"] = result["regression"]
    return json.dumps(out, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys
    r = run_bench(compute_metrics="--metrics" in sys.argv)
    print(bench_summary(r))
    sys.exit(0 if not r["failed"] and r.get("regression", {}).get("ok", True) else 1)
