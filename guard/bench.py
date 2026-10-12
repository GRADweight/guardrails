"""Guard-Bench — dokumentiertes, wiederholbares Testkorpus.

Die Cases in `bench_data/guard-bench.json` sind der objektive Nachweis,
dass der Erstfilter das tut, was er verspricht — und die ehrliche Grenze,
was er NICHT erkennt (Kategorie `edge`/gewisse `adv`: Erwartung =
"pass" = dokumentiertes Entkommen, kein Zufall).

Kategorien:
  legit   Legitime Nutzer-Anfragen.
  inj     Klassische Prompt-Injection-Varianten.
  adv     Umgehungs-Versuche (Encodierung, Whitespace, Zeilenumbruch,
          Uppercase, Zitat).
  edge    Grauzonen (Metasprache, Zitate, Architektur-Fragen).

Lauf:
  python3 -m guard bench                     # Bench + Summary
  python3 -m guard "<eigener Input>"         # Einzelprüfung
  python3 guardrails/guard.py "<Input>"      # Legacy-Modus bleibt lauffähig
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .core import detect_prompt_injection

BENCH_FILE = Path(__file__).resolve().parent / "bench_data" / "guard-bench.json"


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


def run_bench(cases: list[dict] | None = None) -> dict:
    """Führt alle Cases deterministisch durch.

    Rückgabe: {"passed": int, "failed": [ {id, input, expected, got, note} ], "total": int}
    """
    cases = cases if cases is not None else load_bench()
    failed = []
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
    return {"passed": len(cases) - len(failed), "failed": failed, "total": len(cases)}


def bench_summary(result: dict) -> str:
    """Menschenlesbare Summary (für CI + `python3 -m guard bench`)."""
    if result["failed"]:
        lines = [f"GUARD-BENCH: {result['passed']}/{result['total']} grün"]
        for f in result["failed"]:
            lines.append(
                f"  ROT  {f['id']:8} expected={f['expected']:<5} got={f['got']:<5}  # {f['note']}"
            )
        return "\n".join(lines)
    return f"GUARD-BENCH: {result['total']}/{result['total']} grün"


def format_bench_json(result: dict) -> str:
    """Maschinenlesbares Ergebnis (CI-Log, Machine-Readable)."""
    return json.dumps(
        {
            "name": "GRADweight Guard-Bench",
            "passed": result["passed"],
            "failed": result["total"] - result["passed"],
            "total": result["total"],
            "details": result["failed"],
        },
        ensure_ascii=False,
        indent=2,
    )


if __name__ == "__main__":
    # Direkter Aufruf: python3 guard/bench.py
    r = run_bench()
    print(bench_summary(r))
    sys.exit(0 if not r["failed"] else 1)
