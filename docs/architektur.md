# Architektur

## Schichten

| Schicht | Modul | Aufgabe |
|---|---|---|
| Normalisierung | `normalize.py` | Mehrere Sichten auf den Text mit Rückabbildung auf das Original |
| Dekodierung | `decode.py` | Eingebettete Kodierungen finden, begrenzt dekodieren, rekursiv prüfen |
| Regeln | `rules.py`, `lexicon.py` | Regelfamilien mit stabilen IDs, mehrsprachiger Wortschatz |
| Engine | `engine.py` | Regeln auf Sichten anwenden, Kontextregeln, Risikowert |
| Tool-Policy | `tool_policy.py` | Shell, SQL, URL, Pfad; getrennt von der Injection-Erkennung |
| Pipeline | `guard.py` | Schwellen, LLM-Judge, fail-closed, Audit-Hook |
| Judge | `judge.py` | OpenAI-kompatibler Adapter mit Datamarking und strengem Schema |
| Spotlighting | `spotlight.py` | Datamarking, Begrenzer, Base64 für nicht vertrauenswürdige Inhalte |
| Output | `output.py`, `pii.py` | Canary, System-Prompt-Überlappung, Personendaten, Bilder |
| Benchmark | `evaluation.py`, `cli.py` | Datensätze, Metriken, Bericht, Regressions-Gate |

## Normalisierung

Regeln sehen nie den Rohtext, sondern Sichten:

| Sicht | Inhalt | wann |
|---|---|---|
| `text` | NFKD ohne diakritische Zeichen, casefold, unsichtbare Formatzeichen entfernt, kyrillische und griechische Doppelgänger auf Latein abgebildet, Leerraum zusammengefasst (Zeilenumbrüche bleiben) | immer |
| `words` | wie `text`, Satzzeichen als Leerzeichen | immer |
| `leet` | Leetspeak in Wörtern mit Buchstaben aufgelöst (`1gn0r3` → `ignore`) | wenn solche Wörter vorkommen |
| `compact` | Sperrschrift aufgehoben (`i g n o r e`), höchstens 4000 Zeichen | wenn mindestens drei Einzelzeichen folgen |
| `typo` | Anagramme von Schlüsselwörtern korrigiert (`Igonriere` → `ignoriere`) | wenn ein Wort ein Anagramm ist |
| `rejoin` | zerteilte Schlüsselwörter zusammengefügt (`prev ious` → `previous`) | wenn Teile ein Schlüsselwort ergeben |
| `rot13`, `reversed` | ROT13 bzw. rückwärts gelesen | wenn ein Abschnitt kaum Funktionswörter enthält |

Jedes Zeichen einer Sicht kennt seine Position im Original. Treffer werden deshalb immer als
Spanne im Originaltext berichtet. Treffer, die nur in `leet`, `compact`, `typo`, `rejoin`,
`rot13` oder `reversed` entstehen, gelten als absichtlich verschleiert und werden mindestens als
HIGH gewertet (zusätzlicher Befund `OBF-005`).

## Dekodierung

Base64 (auch URL-sicher und ohne Padding), Hex (roh, `\x`, getrennt), URL-Kodierung,
HTML-Entities, `\uXXXX`-Escapes und Unicode-Tag-Zeichen werden erkannt. Ein Segment gilt nur als
Text, wenn es gültiges UTF-8 ist und überwiegend aus druckbaren Zeichen und Buchstaben besteht.
Dekodierte Segmente werden mit allen Regeln erneut geprüft; Treffer zeigen auf das kodierte
Segment im Original und gelten mindestens als HIGH.

Begrenzungen gegen Rechenzeit-Angriffe: Tiefe 2, höchstens 16 Segmente und 65 536 dekodierte
Zeichen insgesamt (in `EngineConfig` einstellbar) sowie höchstens 8192 Zeichen je Segment. Wird das
Budget erschöpft, entsteht der Befund `LIM-002`. Eingaben über `max_input_chars` (Standard
50 000) werden gekürzt geprüft und mindestens auf REVIEW gesetzt (`LIM-001`).

## Regeln und Kontext

Regeln sind Familien statt fester Sätze: Verb + bis zu n Wörter + Qualifizierer + Nomen, mit
Wortschätzen in vier Sprachen, die auch gemischt auftreten dürfen
(«Ignore toutes les instructions précédentes»). Validatoren verwerfen typische harmlose Muster:

- Verneinung, grammatisch gebunden («vergiss nicht», «don't forget», «n'oublie pas»,
  «non dimenticare»); ein einzelnes vorangestelltes Wort genügt nicht.
- Selbstkorrektur («vergiss meine vorherige Anweisung»).
- allgemeine Erwähnung («Wie schreibe ich einen guten Systemprompt?»).
- Gerätebezug beim Entwicklermodus («… auf Android»).
- Zweckangabe in technischer Doku («To send data to the API, POST …»).

Kontextregeln im Chat: Steht ein Treffer in Anführungszeichen und spricht der Text über Angriffe,
sinkt der Schweregrad um eine Stufe (Erwähnung statt Verwendung, Ergebnis meist REVIEW). Fragt
jemand, was ein Chat-Template-Token bedeutet, sinkt er um zwei Stufen. Fragen in der ersten Person
(«Wie sende ich …?») senken Exfiltrations- und Tool-Befunde um zwei Stufen. In Dokumenten gelten
diese Abschwächungen nicht; dort zählen Anweisungen an eine KI stärker.

## Risikowert und Entscheidung

Gewichte je Schweregrad: low 0.2, medium 0.5, high 0.75, critical 0.95. Der Risikowert ist
1 − Π(1 − Gewicht) über den höchsten Schweregrad je Regel-ID. Mehrfachtreffer derselben Regel
erhöhen ihn also nicht, unabhängige Befunde schon. Standardschwellen: REVIEW ab 0.4, BLOCK ab
0.7. Damit gilt: ein HIGH-Befund blockiert, ein MEDIUM-Befund führt zu REVIEW, zwei unabhängige
MEDIUM-Befunde blockieren, LOW-Befunde allein ändern nichts.

## LLM-Judge

Der Judge wird nur bei REVIEW gefragt (Modus `uncertain`) oder zusätzlich bei ALLOW (Modus
`always`), nie bei BLOCK. Er erhält:

1. einen System-Prompt mit Aufgabe, Kategorien, Antwortschema und dem Hinweis, dass der Text
   Daten und keine Anweisungen sind;
2. die Regel-IDs der Vorprüfung (vertrauenswürdig, ausserhalb des Datenbereichs);
3. den Text zwischen zufälligen Begrenzern, mit jedem Leerraum durch eine zufällige Markierung
   ersetzt. Zeichenfolgen, die wie Begrenzer aussehen, werden vorher entfernt.

Die Antwort muss genau die Felder `verdict`, `category`, `confidence` und `reason` haben;
`benign` verlangt `category = "none"`. Alles andere ist ein Fehler. Wiederholt werden
Zeitüberschreitungen, Verbindungsfehler, HTTP 408/409/425/429/5xx und ungültige Antworten, mit
exponentiellem Backoff und Jitter bis `max_retries` und `total_timeout`. Weiterleitungen werden
nicht verfolgt, damit ein API-Schlüssel nicht an ein anderes Ziel geht.

## Audit

Der Audit-Hook erhält je Entscheidung ein `AuditEvent` mit Zeitstempel (UTC), Kontext,
Entscheidung, Regel-IDs, Judge-Ergebnis, SHA-256 und Länge der Eingabe. Klartext nur mit
`audit_include_text=True`. Fehler im Hook werden protokolliert; mit `strict_audit=True` führt ein
fehlgeschlagener Hook zu BLOCK.
