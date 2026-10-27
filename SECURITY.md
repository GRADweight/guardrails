# Sicherheit

## Schwachstellen melden

Bitte melden Sie Schwachstellen nicht über öffentliche Issues, sondern vertraulich:

- über GitHub Private Vulnerability Reporting («Security» → «Report a vulnerability») in diesem
  Repository, oder
- per E-Mail an mail@gradweight.ch.

Hilfreich sind: betroffene Version, ein minimales Beispiel und die beobachtete Wirkung. Wir
bestätigen den Eingang in der Regel innerhalb von fünf Arbeitstagen und stimmen eine
Veröffentlichung mit Ihnen ab.

## Was als Schwachstelle gilt

- Eingaben, die zu Abstürzen, unbegrenzter Laufzeit oder unbegrenztem Speicherverbrauch führen.
- Fälle, in denen die Pipeline trotz Judge-Fehler freigibt (Verletzung von fail-closed).
- Abfluss von Eingaben oder Schlüsseln über Protokolle, Fehlermeldungen oder den Judge-Transport.
- Fehler in den Prüfziffern, die gültige Personendaten ungeschwärzt lassen.

Eine einzelne neue Formulierung, die von den Regeln nicht erkannt wird, ist eine erwartbare Grenze
regelbasierter Erkennung (siehe `docs/grenzen.md`). Solche Fälle nehmen wir gerne als Issue mit
Beispiel entgegen; sie werden in das Dev-Set aufgenommen.

## Unterstützte Versionen

Sicherheitskorrekturen erhält die jeweils neueste Version 2.x.
