#!/usr/bin/env python3
"""Einmaligen Snapshot-Schrieb: erzeugt `guard/bench_data/guard-bench-baseline.json`
aus dem aktuellen grünen Zustand. Nur für Setup, nicht im Normalbetrieb."""
import json, sys
from pathlib import Path

# guard-Paketzugriff
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from guard.bench import run_bench, BENCH_FILE, BASE_FILE  # type: ignore

r = run_bench(compute_metrics=True)
if r.get("failed"):
    print("Bench NICHT grün — keine Baseline schreiben!", r["failed"], file=sys.stderr)
    sys.exit(1)
# nur FP/FN pro Kategorie
base = {cat: {"fp": m["fp"], "fn": m["fn"]} for cat, m in r["metrics"].items()}
# expect-basierte Metriken klarer: TP/FP/TN/FN
print("Erzeuge Baseline:", json.dumps(base, ensure_ascii=False, indent=2))
with open(BASE_FILE, "w", encoding="utf-8") as f:
    json.dump({"source": BENCH_FILE.name, "created": "2026/10/19", "metrics": base}, f, ensure_ascii=False, indent=2)
print(f"Geschrieben: {BASE_FILE}")
