# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Die übergeordneten Regeln stehen in `../CLAUDE.md` (Schweizer Hochdeutsch mit ss, ein Repo pro Sitzung, nie auf main pushen usw.) und gelten hier zusätzlich.

## Was dieses Repo ist

Zwei Dinge in einem öffentlichen Repo:

1. **Guard-Baustein** (Python, null externe Abhängigkeiten, Python ≥ 3.8): deterministischer Erstfilter vor dem LLM-Aufruf — Prompt-Injection per Signatur-Substring, Vertraulichkeits-Erkennung auf Retrieval-Chunks, quell-zitierte Antwort bzw. ehrliche Nicht-Antwort.
2. **Fundament-Doku** der Praxis auf Deutsch (`README.md`, `docs/*.md`): Künste, Grenzen, Referenzen, Schweizer Regulierung mit Fristen.

## Befehle

```bash
python3 guardrails/guard.py                  # Standalone-Selbsttest, ohne Installation
python3 guardrails/guard.py "<Text>"         # Einzelprüfung (Standalone)

pip install -e ".[dev]"                      # Paket + pytest
python -m guard bench                        # Guard-Bench, Exit 1 bei rotem Case
python -m guard bench --json                 # maschinenlesbar
python -m guard "<Text>"                     # Einzelprüfung
pytest tests                                 # ganze Suite
pytest tests/test_guard_core.py::TestDetectPromptInjection -k devmode   # einzelner Test
```

CI (`.github/workflows/guard-selftest.yml`, Py 3.9/3.11/3.12) führt Standalone-Selbsttest, Bench, pytest und Einzel-CLI-Checks aus; Letztere greppen auf die Ausgabe `Injection erkannt: True/False` — dieses Format nicht ändern, ohne die CI anzupassen.

## Architektur

- `guard/core.py` — die Kernfunktionen `detect_prompt_injection`, `is_confidential`, `format_rag_response` plus die Konstanten `INJECTION_SIGNATURES`, `CONFIDENTIAL_LEVELS`, `DEMO_CHUNKS`. Re-Exporte in `guard/__init__.py` (`__all__`, `__version__`).
- `guard/bench.py` — lädt `guard/bench_data/guard-bench.json` (Schema je Case: `id`, `input`, `expect: block|pass`, `note`) und vergleicht gegen `detect_prompt_injection`.
- `guard/__main__.py` — CLI; ohne Argument oder mit `bench` läuft die Bench, sonst wird der Text geprüft.
- `guardrails/guard.py` — **Standalone-Kopie** derselben Logik (Legacy, ohne Paketimport) mit eigenem `_selftest()`. Die Signaturliste (`_INJECTION_SIGNATURES`) und `_CONFIDENTIAL` sind dupliziert; kein Test erzwingt Gleichheit. Änderungen an Signaturen oder Logik in **beiden** Dateien nachziehen.

### Guard-Bench: Grenzen sind Absicht

Die Bench dokumentiert auch, was der Filter **nicht** erkennt: `adv-01…03` (Base64, Whitespace-Aufweitung, Zeilenumbruch) stehen bewusst auf `expect: pass`. Diese Cases nicht «reparieren», indem man `expect` umstellt oder den Filter still erweitert — eine Verhaltensänderung braucht neue/angepasste Cases mit `note` und Doku-Nachführung. `tests/test_guard_bench.py` verlangt: ≥ 24 Cases, eindeutige IDs, Pflichtfelder inkl. `note`, 32/32 grün.

## Zahlen, die an mehreren Stellen stehen

Case-Anzahl (32), Kategorienverteilung (legit 12 / inj 10 / adv 5 / edge 5), Testanzahl (47) und Version (1.3.0) stehen in `README.md`, `QUICKSTART.md`, `pyproject.toml` (description, version), `guard/__init__.py` (`__version__`), CI-Workflow und `CHANGES.md`. Bei Änderungen alle nachziehen. (Der Modul-Docstring in `guard/__init__.py` nennt noch «24 Cases» — veraltet.)

## Doku-Konventionen (aus CONTRIBUTING.md)

- Jede inhaltliche Änderung (Code-Verhalten, Doku, Norm-Frist, Grenze) bekommt einen Eintrag in `CHANGES.md` im dort definierten Format (`## YYYY/MM/DD — …`, Doku/Was/Quelle/Commit), neueste oben.
- Norm-Fristen immer mit Datum **und** Quelle; nichts aus dem Gedächtnis.
- Grenzen bleiben in der jeweiligen Doku sichtbar (nicht in einen Anhang verschieben).
- Verbotene Begriffe: «KI-Magie», «AI-Sprite», «KI-Plattform», «wir sind die besten/führend», «wir automatisieren alles», unbelegte Zahlen. Keine Preise, Kunden oder internen Zahlen — das Repo ist öffentlich.
- Doku auf Deutsch; Code-Kommentare dürfen Englisch sein.
- Interne Dokumente (`material/`, Sitzungs-Management wie früher `PROJEKT.md`) gehören nach `grad-internal-kb`, nicht hierher.

## Rahmen
- Öffentliches Repo von GRADweight. Alles, was hier landet, sieht jeder.
- Nie aufnehmen: Preise, Kundennamen, Kundendaten, interne Decks, Schlüssel.
  Internes gehört nach grad-internal-kb.
- Beispiele und Tests nur mit erfundenen oder öffentlichen Daten.
- Kontakt in Texten nur gradweight.ch.

## Ablauf
- Ein Auftrag, ein Branch `<typ>/<thema>` von origin/main. Nie auf main.
- Nach jedem grünen Schritt selbst committen und den eigenen Branch pushen,
  ohne Rückfrage. Am Ende den Pull Request mit `gh pr create` öffnen.
- Conventional Commits auf Deutsch mit «weil».
- Fertig heisst: Tests grün, ruff sauber, `gitleaks protect --staged` sauber,
  PR offen, CI grün. Schlussmeldung kurz: PR-Link, was geändert, was offen.
- Tests immer mit `uv run pytest`, nie mit dem System-Python.
