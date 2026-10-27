# Beitragen

Beiträge sind willkommen: neue Angriffs- und Gegenbeispiele, Regeln, Fehlerkorrekturen und
Verbesserungen der Dokumentation.

## Einrichtung

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
```

## Vor jedem Pull Request

```bash
ruff check . && ruff format --check .
mypy
pytest --cov
python scripts/generate_reports.py --check
```

Alle Befehle müssen ohne Fehler durchlaufen; die Testabdeckung des Pakets muss mindestens 90 %
betragen. Tests dürfen kein Netzwerk verwenden (ausser einem lokalen Server auf 127.0.0.1).

## Regeln und Benchmark

- Neue Fälle kommen in `bench/data/dev.jsonl`. Das Holdout-Set (`bench/data/holdout.jsonl`)
  wird nicht verändert und nicht zum Abstimmen von Regeln verwendet; seine Prüfsumme wird getestet.
- Regel-IDs sind stabil. Eine geänderte Regel behält ihre ID, eine entfernte ID wird nicht neu
  vergeben.
- Nach Änderungen an Regeln `python scripts/generate_reports.py` ausführen und die erzeugten
  Dateien mitcommitten. Verschlechtert sich eine Metrik über die Toleranz, schlägt das Gate fehl;
  eine neue Baseline (`--update-baseline`) braucht eine Begründung im Pull Request.
- Jede Zahl in der Dokumentation muss aus einem Skript stammen oder von einem Test geprüft werden.

## Stil

- Code: englische Bezeichner, deutsche Docstrings und Kommentare, vollständig typisiert.
- Dokumentation: Schweizer Hochdeutsch («ss», echte Umlaute), sachlich und knapp.
- Commits: kurze Betreffzeile auf Deutsch, Begründung im Text.

Kontakt: mail@gradweight.ch
