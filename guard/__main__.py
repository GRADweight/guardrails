"""`python3 -m guard` — CLI-Einstieg.

Modi:
  python3 -m guard                          # Guard-Bench (Summary + Exit-Code)
  python3 -m guard bench                    # Guard-Bench, identisch (Alias)
  python3 -m guard bench --json             # Guard-Bench, maschinenlesbar
  python3 -m guard "<eigener Text>"         # Einzelprüfung (1 String)
  python3 -m guard --version                # Paket-Version
"""
from __future__ import annotations

import sys

import guard
from guard.bench import run_bench, bench_summary, format_bench_json


def _main(argv: list[str]) -> int:
    if not argv or argv[0] in ("bench", "-b", "--bench"):
        if argv and argv[-1] == "--json":
            print(format_bench_json(run_bench()))
        else:
            print(f"guard v{guard.__version__}")
            print(bench_summary(run_bench()))
        r = run_bench()
        return 0 if not r["failed"] else 1

    if argv[0] in ("--version", "-v"):
        print(f"guard {guard.__version__}")
        return 0

    if argv[0] in ("-h", "--help"):
        print((__doc__ or "guard — Guardrails-CLI").strip())
        return 0

    # Einzelprüfung: alles ausser Optionen = Text
    text = " ".join(a for a in argv if not a.startswith("-"))
    from guard.core import detect_prompt_injection

    hit = detect_prompt_injection(text)
    print(f"Input:             {text!r}")
    print(f"Injection erkannt: {hit}")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
