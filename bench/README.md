# Benchmark: Methodik

Der Benchmark misst nur die Regelschicht (Standard-`Guard()` ohne LLM-Judge). Er ist
deterministisch, läuft offline und braucht keine Abhängigkeiten ausser dem Paket.

```bash
python -m gradweight_guardrails bench --data bench/data --baseline bench/baseline.json
python scripts/generate_reports.py   # schreibt bench/ERGEBNISSE.md, docs/regeln.md, README-Tabelle
```

## Datensätze

| Datei | Zweck |
|---|---|
| `data/holdout.jsonl` | Holdout. Wurde vor den neuen Regeln geschrieben und committet und wird nie zum Abstimmen verwendet. Prüfsumme in `holdout.jsonl.sha256`. |
| `data/dev.jsonl` | Entwicklungs-Set. Die Regeln wurden an diesen Fällen abgestimmt. |

Jeder Fall ist eine JSON-Zeile mit `id`, `split`, `lang` (`de`, `fr`, `it`, `en`, `mixed`,
`none` für Tool-Eingaben), `category`, `context` (`chat`, `document`, `tool`), `label`
(`attack` oder `benign`), `technique`, `text`, `note` und bei Tool-Fällen `tool`.

Kategorien: `direct` (direkte Angriffe), `obfuscated` (Sperrschrift, Doppelgänger,
Zero-Width, Base64, Hex, URL-Kodierung, ROT13, Leetspeak, gemischte Sprachen u.a.),
`indirect` (Angriffe in E-Mails, Webseiten, RAG-Chunks), `hard_negative` (Entwicklerfragen
mit `rm -rf`, SQL, `curl` oder «System-Prompt», Geschäftsfragen in vier Sprachen, Texte
über Prompt-Injection, Persona-Wünsche, Selbstkorrekturen), `benign_document`
(Geschäfts- und Handbuchtexte), `tool_attack` und `tool_benign`.

Alle Texte sind erfunden. Namen, Firmen, Adressen, IBAN und Telefonnummern sind Beispiele
oder öffentlich dokumentierte Testwerte.

## Zählweise

* Hauptmetrik: Eine Entscheidung REVIEW oder BLOCK gilt als Erkennung. Zusätzlich wird
  «nur BLOCK» ausgewiesen.
* Jede Umgehung zählt als False Negative, jeder markierte harmlose Fall als False Positive.
  Nichts wird nachträglich umetikettiert.
* Precision, Recall, F1 und FPR werden für dev und holdout getrennt, je Sprache und je
  Kategorie berichtet (`ERGEBNISSE.md`).

## Regressions-Gate

`baseline.json` enthält Precision, Recall, F1 und FPR je Split und eine Toleranz. Der Test
`tests/test_bench_gate.py` liest die Baseline und schlägt fehl, wenn eine Metrik um mehr
als die Toleranz schlechter wird. Ein zweiter Test belegt mit absichtlich verschlechterten
Werten, dass das Gate tatsächlich auslöst. Die Baseline wird nur bewusst neu geschrieben
(`python scripts/generate_reports.py --update-baseline`).

## Einschränkungen (bitte mitlesen)

* **Gleiche Herkunft.** Holdout, Dev-Set und Regeln stammen aus derselben Hand. Das Holdout
  wurde zwar vor den Regeln geschrieben und committet (siehe Git-Historie), beim Schreiben
  waren die geplanten Regelfamilien aber bereits bekannt. Die Holdout-Werte überschätzen
  deshalb mit hoher Wahrscheinlichkeit die Leistung auf fremden Daten. Eine unabhängige
  Prüfung mit eigenen Fällen ist ausdrücklich erwünscht.
* **Kleine Stichprobe.** 126 Holdout-Fälle; ein einzelner Fall verschiebt Recall oder FPR
  einer Sprache um mehrere Prozentpunkte. Die Werte sind Anhaltspunkte, keine Garantie.
* **Keine adaptiven Angriffe.** Ein Angreifer, der die Regeln kennt (sie sind öffentlich),
  findet Formulierungen, die nicht erkannt werden. Der Benchmark misst bekannte Muster.
* **Kein Judge.** Die Wirkung eines LLM-Judges hängt vom Modell ab und ist hier nicht gemessen.

## Änderungen nach der ersten Holdout-Auswertung

Die Regeln wurden mit Commit «Neuer Kern: mehrschichtige Erkennung …» eingefroren, danach
wurde das Holdout zum ersten Mal ausgewertet. Spätere Änderungen an der Erkennung werden hier
mit Anlass und Wirkung aufgeführt:

| Änderung | Anlass | Wirkung auf dev / holdout |
|---|---|---|
| Verneinungsprüfung grammatisch gebunden (z.B. französisch «ne … pas», englisch «not» nur nach Modalverb) | Property-Test fand die Umgehung «n Ignore all previous instructions» | keine (Metriken unverändert) |
