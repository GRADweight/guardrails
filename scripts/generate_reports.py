#!/usr/bin/env python3
"""Erzeugt alle generierten Dokumente aus dem Code.

* ``bench/ERGEBNISSE.md``: Benchmark-Bericht (dev und holdout getrennt)
* ``docs/regeln.md``: Regelkatalog
* README-Block zwischen ``<!-- BENCH:START -->`` und ``<!-- BENCH:END -->``

Aufruf: ``python scripts/generate_reports.py`` (schreibt) oder ``--check`` (prüft nur, Exit 1
bei Abweichung). Die Baseline ``bench/baseline.json`` wird nur mit ``--update-baseline``
neu geschrieben, nie automatisch.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gradweight_guardrails import __version__
from gradweight_guardrails.catalog import render_catalog
from gradweight_guardrails.evaluation import (
    CaseResult,
    evaluate,
    load_cases,
    make_baseline,
    readme_block,
    render_report,
    sha256_file,
)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "bench" / "data"
REPORT = ROOT / "bench" / "ERGEBNISSE.md"
RULES_DOC = ROOT / "docs" / "regeln.md"
README = ROOT / "README.md"
BASELINE = ROOT / "bench" / "baseline.json"
START, END = "<!-- BENCH:START -->", "<!-- BENCH:END -->"


def results() -> dict[str, list[CaseResult]]:
    return {split: evaluate(load_cases(DATA / f"{split}.jsonl")) for split in ("dev", "holdout")}


def expected_files(res: dict[str, list[CaseResult]]) -> dict[Path, str]:
    hashes = {f"{split}.jsonl": sha256_file(DATA / f"{split}.jsonl") for split in res}
    files = {
        REPORT: render_report(res, dataset_hashes=hashes, version=__version__),
        RULES_DOC: render_catalog(),
    }
    readme = README.read_text("utf-8")
    if START in readme and END in readme:
        head, rest = readme.split(START, 1)
        _, tail = rest.split(END, 1)
        files[README] = f"{head}{START}\n{readme_block(res)}\n{END}{tail}"
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="nur prüfen, nichts schreiben")
    parser.add_argument("--update-baseline", action="store_true", help="bench/baseline.json neu schreiben")
    args = parser.parse_args(argv)
    res = results()
    stale = []
    for path, content in expected_files(res).items():
        current = path.read_text("utf-8") if path.exists() else None
        if current != content:
            stale.append(path.relative_to(ROOT))
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, "utf-8")
    if args.update_baseline and not args.check:
        BASELINE.write_text(json.dumps(make_baseline(res), indent=2) + "\n", "utf-8")
        print(f"Baseline geschrieben: {BASELINE.relative_to(ROOT)}")
    if args.check and stale:
        print("Veraltet:", ", ".join(map(str, stale)), file=sys.stderr)
        return 1
    print("Aktualisiert:" if stale else "Unverändert.", ", ".join(map(str, stale)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
