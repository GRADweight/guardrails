"""Kommandozeile: ``python -m gradweight_guardrails scan|bench|rules``.

Exit-Codes von ``scan``: 0 = ALLOW, 3 = REVIEW, 4 = BLOCK.
Exit-Code von ``bench``: 0 = ok, 1 = Regression gegenüber der Baseline.
Exit-Code 2 bei Bedien- und Eingabefehlern (falsche Argumente, fehlende oder ungültige Dateien,
nicht lesbare Eingabe); dann erscheint eine Meldung auf stderr, kein Traceback.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .catalog import catalog
from .evaluation import (
    check_baseline,
    evaluate,
    load_cases,
    make_baseline,
    metrics_for,
    render_report,
    sha256_file,
)
from .guard import Guard
from .models import Decision, ScanResult

__all__ = ["main"]

EXIT_CODES = {Decision.ALLOW: 0, Decision.REVIEW: 3, Decision.BLOCK: 4}
EXIT_USAGE = 2
SPLITS = ("dev", "holdout")


def _print_result(result: ScanResult, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return
    decision = result.decision.value.upper()
    print(f"Entscheidung: {decision}  (Risikowert {result.score:.2f}, Kontext {result.context.value})")
    for finding in result.findings:
        print(
            f"  {finding.rule_id:8} {finding.severity.value:8} {finding.category.value:22} "
            f"{finding.language:5} [{finding.span[0]}:{finding.span[1]}] {finding.layer}: {finding.excerpt!r}"
        )
    for reason in result.reasons:
        print(f"  Grund: {reason}")


def _cmd_scan(args: argparse.Namespace) -> int:
    text = sys.stdin.read() if args.text in (None, "-") else args.text
    guard = Guard()
    if args.tool:
        result = guard.scan_tool_input(text, args.tool)
    elif args.document:
        result = guard.scan_document(text)
    else:
        result = guard.scan(text)
    _print_result(result, args.json)
    return EXIT_CODES[result.decision]


def _cmd_bench(args: argparse.Namespace) -> int:
    data = Path(args.data)
    splits = SPLITS if args.split == "all" else (args.split,)
    results = {}
    hashes = {}
    for split in splits:
        path = data / f"{split}.jsonl"
        if not path.exists():
            print(f"Fehler: Datensatz fehlt: {path}", file=sys.stderr)
            return EXIT_USAGE
        results[split] = evaluate(load_cases(path))
        hashes[path.name] = sha256_file(path)
    if args.json:
        out = {name: metrics_for(res).as_dict() for name, res in results.items()}
        print(json.dumps(out, indent=2))
    else:
        print(f"gradweight-guardrails {__version__}")
        for name, res in results.items():
            m = metrics_for(res)
            b = metrics_for(res, blocked_only=True)
            print(
                f"  {name:8} n={m.n:4}  precision={_fmt(m.precision)}  recall={_fmt(m.recall)}  "
                f"f1={_fmt(m.f1)}  fpr={_fmt(m.fpr)}  recall(block)={_fmt(b.recall)}"
            )
    if args.report:
        Path(args.report).write_text(render_report(results, dataset_hashes=hashes, version=__version__), "utf-8")
    if args.update_baseline:
        Path(args.update_baseline).write_text(json.dumps(make_baseline(results), indent=2) + "\n", "utf-8")
    if args.baseline:
        gate = check_baseline(results, json.loads(Path(args.baseline).read_text("utf-8")))
        if not gate.ok:
            print("Regression gegenüber der Baseline:", file=sys.stderr)
            for failure in gate.failures:
                print(f"  {failure}", file=sys.stderr)
            return 1
        print("Baseline: keine Regression")
    return 0


def _fmt(value: float | None) -> str:
    return "  –  " if value is None else f"{value:.3f}"


def _cmd_rules(args: argparse.Namespace) -> int:
    entries = catalog()
    if args.json:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
        return 0
    for entry in entries:
        print(
            f"{entry['id']:9} {entry['scope']:15} {entry['category']:22} {entry['severity']:28} {entry['description']}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gradweight-guardrails",
        description="Prompt-Injection-Abwehr (DE/FR/IT/EN): prüfen, Benchmark, Regelkatalog.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="Text prüfen (Exit 0/3/4 = allow/review/block)")
    p_scan.add_argument("text", nargs="?", help="zu prüfender Text; ohne Angabe oder '-' von stdin")
    group = p_scan.add_mutually_exclusive_group()
    group.add_argument("--document", action="store_true", help="als Dokument prüfen (indirekte Injection)")
    group.add_argument("--tool", choices=["shell", "sql", "url", "path"], help="als Tool-Eingabe prüfen")
    p_scan.add_argument("--json", action="store_true", help="Ergebnis als JSON")
    p_scan.set_defaults(func=_cmd_scan)

    p_bench = sub.add_parser("bench", help="Benchmark auf bench/data ausführen")
    p_bench.add_argument("--data", default="bench/data", help="Verzeichnis mit dev.jsonl und holdout.jsonl")
    p_bench.add_argument("--split", choices=["dev", "holdout", "all"], default="all")
    p_bench.add_argument("--report", help="Markdown-Bericht schreiben (z.B. bench/ERGEBNISSE.md)")
    p_bench.add_argument("--baseline", help="gegen diese Baseline prüfen (Exit 1 bei Regression)")
    p_bench.add_argument("--update-baseline", help="Baseline aus den aktuellen Ergebnissen schreiben")
    p_bench.add_argument("--json", action="store_true", help="Metriken als JSON")
    p_bench.set_defaults(func=_cmd_bench)

    p_rules = sub.add_parser("rules", help="Regelkatalog anzeigen")
    p_rules.add_argument("--json", action="store_true")
    p_rules.set_defaults(func=_cmd_rules)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        code: int = args.func(args)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        # Eingabefehler (Datei fehlt, ungültiges JSON/JSONL, falsche Kodierung) sauber melden.
        print(f"Fehler: {type(exc).__name__}: {exc}", file=sys.stderr)
        return EXIT_USAGE
    return code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
