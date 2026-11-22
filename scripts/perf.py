#!/usr/bin/env python3
"""Mikrobenchmark der Regelschicht (ohne LLM-Judge, ohne Netz, ohne künstliche Wartezeiten).

Misst die Laufzeit von ``Guard.scan``/``scan_document``/``scan_tool_input`` für alle Texte
aus ``bench/data`` (mehrere Durchläufe, Reihenfolge je Durchlauf gemischt) sowie für drei
synthetische längere Texte. Ergebnis: p50/p95/p99 je Aufruf und Durchsatz (ein Thread).

Schreibt ``bench/PERFORMANCE.md`` und den README-Block zwischen ``<!-- PERF:START -->`` und
``<!-- PERF:END -->``. Die Zahlen hängen vom Rechner ab; Datum, CPU und Python-Version
werden mitgeschrieben.
"""

from __future__ import annotations

import argparse
import os
import platform
import random
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path

from gradweight_guardrails import Guard, __version__
from gradweight_guardrails.engine import warmup
from gradweight_guardrails.evaluation import Case, load_cases

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "bench" / "PERFORMANCE.md"
README = ROOT / "README.md"
START, END = "<!-- PERF:START -->", "<!-- PERF:END -->"

BUSINESS = (
    "Sehr geehrte Damen und Herren, besten Dank für Ihre Offerte vom 12. Oktober. Wir bitten Sie, "
    "die Positionen 3 bis 7 bis Ende Monat zu liefern und die Rechnung mit QR-Zahlteil zu senden. "
)


def _cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text("utf-8").splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def _percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(q * (len(ordered) - 1))))
    return ordered[index]


def _run(guard: Guard, case: Case) -> None:
    if case.context == "chat":
        guard.scan(case.text)
    elif case.context == "document":
        guard.scan_document(case.text)
    else:
        guard.scan_tool_input(case.text, case.tool or "shell")


def _load() -> str:
    try:
        one, five, _ = os.getloadavg()
    except OSError:
        return "unbekannt"
    return f"{one:.2f} (1 min) / {five:.2f} (5 min) bei {os.cpu_count()} Kernen"


def measure(rounds: int, seed: int) -> dict[str, object]:
    load_before = _load()
    cases = load_cases(ROOT / "bench" / "data" / "dev.jsonl") + load_cases(ROOT / "bench" / "data" / "holdout.jsonl")
    guard = Guard()
    started = time.perf_counter()
    warmup()
    warmup_ms = (time.perf_counter() - started) * 1000
    rng = random.Random(seed)  # noqa: S311 - nur Reihenfolge der Messung
    latencies: dict[str, list[float]] = {"chat": [], "document": [], "tool": []}
    total_calls = 0
    total_time = 0.0
    for _ in range(rounds):
        order = list(cases)
        rng.shuffle(order)
        for case in order:
            t0 = time.perf_counter_ns()
            _run(guard, case)
            elapsed = (time.perf_counter_ns() - t0) / 1e6
            latencies[case.context].append(elapsed)
            total_calls += 1
            total_time += elapsed / 1000
    synthetic: dict[str, list[float]] = {}
    for label, text in (
        ("1 000 Zeichen", (BUSINESS * 6)[:1000]),
        ("10 000 Zeichen", (BUSINESS * 60)[:10000]),
        ("50 000 Zeichen (Obergrenze)", (BUSINESS * 300)[:50000]),
    ):
        samples = []
        for _ in range(max(5, rounds)):
            t0 = time.perf_counter_ns()
            guard.scan_document(text)
            samples.append((time.perf_counter_ns() - t0) / 1e6)
        synthetic[label] = samples
    return {
        "load": load_before,
        "cases": len(cases),
        "rounds": rounds,
        "warmup_ms": warmup_ms,
        "latencies": latencies,
        "synthetic": synthetic,
        "throughput": total_calls / total_time,
    }


def render(result: dict[str, object]) -> tuple[str, str]:
    latencies: dict[str, list[float]] = result["latencies"]  # type: ignore[assignment]
    synthetic: dict[str, list[float]] = result["synthetic"]  # type: ignore[assignment]
    rows = ["| Messung | Aufrufe | p50 | p95 | p99 |", "|---|---:|---:|---:|---:|"]
    labels = {
        "chat": "Benchmark-Texte, Chat",
        "document": "Benchmark-Texte, Dokument",
        "tool": "Benchmark, Tool-Eingaben",
    }
    for key in ("chat", "document", "tool"):
        values = latencies[key]
        rows.append(
            f"| {labels[key]} | {len(values)} | {_percentile(values, 0.5):.2f} ms | "
            f"{_percentile(values, 0.95):.2f} ms | {_percentile(values, 0.99):.2f} ms |"
        )
    for label, values in synthetic.items():
        rows.append(
            f"| Geschäftstext {label} | {len(values)} | {statistics.median(values):.1f} ms | "
            f"{_percentile(values, 0.95):.1f} ms | {_percentile(values, 0.99):.1f} ms |"
        )
    table = "\n".join(rows)
    meta = (
        f"Gemessen am {datetime.now(UTC):%Y-%m-%d} mit `scripts/perf.py`, Version {__version__}, "
        f"Python {platform.python_version()}, {_cpu_model()}, ein Thread, Systemlast beim Start {result['load']}. "
        f"Durchsatz über alle Benchmark-Texte: {result['throughput']:.0f} Aufrufe/s; "
        f"einmaliges Kompilieren der Muster: {result['warmup_ms']:.0f} ms."
    )
    doc = "\n".join(
        [
            "# Performance der Regelschicht",
            "",
            "Diese Datei wird von `scripts/perf.py` erzeugt. Die Werte hängen vom Rechner ab und",
            "werden deshalb nicht in CI geprüft, nur ihr Vorhandensein und ihre Übereinstimmung mit",
            "der README.",
            "",
            "Methode: Alle Texte aus `bench/data` (dev und holdout) werden in "
            f"{result['rounds']} Durchläufen in jeweils zufälliger Reihenfolge geprüft; gemessen wird",
            "jeder einzelne Aufruf mit `time.perf_counter_ns()`. Kein LLM-Judge, kein Netz, keine",
            "künstlichen Wartezeiten. Die Laufzeit eines LLM-Judges kommt bei Bedarf hinzu und hängt",
            "vom Modell und der Infrastruktur ab; sie ist hier nicht gemessen.",
            "",
            meta,
            "",
            table,
            "",
        ]
    )
    readme = f"{meta}\n\n{table}"
    return doc, readme


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--no-write", action="store_true", help="nur ausgeben")
    args = parser.parse_args()
    doc, readme_part = render(measure(args.rounds, args.seed))
    print(doc)
    if not args.no_write:
        OUT.write_text(doc, "utf-8")
        text = README.read_text("utf-8")
        if START in text and END in text:
            head, rest = text.split(START, 1)
            _, tail = rest.split(END, 1)
            README.write_text(f"{head}{START}\n{readme_part}\n{END}{tail}", "utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
