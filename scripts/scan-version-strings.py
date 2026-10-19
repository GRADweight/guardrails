#!/usr/bin/env python3
"""Sucht alle Stellen, wo 32 / 47 / 1.3.0 / 24 vorkommen, in Repo + Doku.
Dient als Checkliste für den Version-Nachzieher."""
import re, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
pats = re.compile(r'\b(32 Cases|32/32|32 dokumentierte|47 (Tests |pytest|Test)|1\.3\.0|24 Cases|11 Signaturen|11 [A-Za-z ]*Signatur)\b')
for p in sorted(root.rglob("*")):
    if p.is_dir() or any(s in str(p) for s in [".venv", ".git", "__pycache__", "egg-info"]):
        continue
    if not p.suffix.lower() in [".md", ".toml", ".yml", ".yaml", ".py", ".txt"]:
        continue
    try:
        for i, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
            if pats.search(line):
                rel = str(p.relative_to(root))
                print(f"{rel}:{i}: {line.strip()}")
    except Exception:
        pass
