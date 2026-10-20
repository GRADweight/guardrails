# AGENTS.md — GRADweight/guardrails

## Zweck
Guard-Baustein der GRADweight GmbH: Signatur-Schicht (deterministisch, null
Netz, null externe Abhängigkeit) plus pluggbarer LLM-Judge, lauffähig als
Paket (`guard/`) und als Standalone (`guardrails/guard.py`). 42
dokumentierte Guard-Bench-Cases in vier Kategorien (legit, inj, adv, edge),
51 pytest-Tests, CI grün auf Python 3.9 / 3.11 / 3.12. Kein Framework-Fetisch.

## Layout
- `guard/core.py`       — Signatur-Schicht (INJECTION_SIGNATURES, detect_prompt_injection)
- `guard/judge.py`      — pluggbares Prüf-Interface (DummyJudge = CI-Default, LLMJudge = Produktion)
- `guard/gate.py`       — GuardPipeline (Signatur -> Prüfer -> GuardResult mit Kategorie + Grund)
- `guard/bench_data/`   — guard-bench.json (42 Cases), guard-bench-baseline.json (Regression-Snapshot)
- `guardrails/guard.py` — Standalone-Selbsttest (keine Installation nötig)
- `tests/`              — 51 pytest-Tests
- `scripts/`            — negative-gate-test.py (beweisbarer Gate-Trigger), perf-benchmark.py
- `.github/workflows/guard-selftest.yml` — CI (Py 3.9 / 3.11 / 3.12), kein Netz nötig
- `docs/`               — ai-craft.md, suverainetaet-schweiz.md, referenzen.md, grenzen.md

## Befehle
```bash
pip install -e .[dev]          # mit pytest-Dev-Extras
python3 -m guard bench         # Guard-Bench: 42 dokumentierte Cases
python3 -m guard "<input>"     # Einzelprüfung
python3 guardrails/guard.py    # Standalone (keine Installation)
pytest -q                      # 51 Tests
```

## Konventionen
- **Sprache**: Schweizer Hochdeutsch, «ss», keine Gedankenstriche — auch in
  Commits und Code-Kommentaren.
- **Secrets**: ausschliesslich via `os.environ` / `LITELLM_MASTER_KEY`, nie in
  Dateien oder Logs. `.env` ist nie zu lesen.
- **Branch-Modell**: `main` = Approved State; Änderungen nur via Squash-PR nach
  Gründer-Freigabe. `agent/<slug>` = laufende Agent-Arbeit.
  `feature/<auftrag>-<slug>` = scoping Extension.
- **Nie anfassen**: `material/` — interne Preismodelle, Decks,
  Angebotskataloge. Gehört nicht in dieses Repo, nie in den git-Index
  (siehe .gitignore), nie in der Historie (filter-repo-Vorgang bevor public).

## CI / Tests
CI-Workflow `guard-selftest.yml` in drei Stufen: Standalone-Selbsttest ->
Guard-Bench -> pytest. 51 Tests, lokal grün.
`scripts/negative-gate-test.py` ist ein beweisbarer Gate-Trigger als
Proof-of-Correctness, kein produktiver Test.

## Status (10/2026)
- v1.4.0: GuardPipeline + Perf-Benchmark (Signatur ~1us / 770k, LLM-Judge ~188ms)
- 51 Tests, 42 Guard-Bench-Cases, CI grün
- Public-Readiness: `material/` git rm --cached auf Branch
  `chore/public-readiness`; repo-Beschreibung gesetzt;
  Visibility-Switch ist Gründer-Entscheidung.
- Noch privat. Launch 25.10.2026 nach Gründer-Entscheid.
