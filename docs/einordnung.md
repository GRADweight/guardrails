# Einordnung: OWASP, EU AI Act, revDSG

Diese Seite ordnet die Funktionen technisch ein. Sie ist keine Rechtsberatung und keine
Konformitätsaussage. Stand der geprüften Quellen: Oktober 2026.

## OWASP Top 10 for LLM Applications 2025

| Risiko | Empfehlung von OWASP (Auszug) | Beitrag dieser Bibliothek |
|---|---|---|
| **LLM01:2025 Prompt Injection** | Eingabe- und Ausgabefilter, externe Inhalte trennen und kennzeichnen, Angriffe testen, Rechte begrenzen, menschliche Freigabe | Regeln für direkte und indirekte Injection (`scan`, `scan_document`), Spotlighting (`spotlight`), Benchmark mit Angriffsfällen, Tool-Policy |
| **LLM02:2025 Sensitive Information Disclosure** | Daten bereinigen, Muster erkennen und schwärzen, Zugriffe begrenzen | `OutputGuard` mit AHV, IBAN, Kreditkarten, E-Mail, Telefon; Audit ohne Klartext |
| **LLM07:2025 System Prompt Leakage** | keine Geheimnisse in den System-Prompt, Kontrollen ausserhalb des Modells | Canary-Tokens, n-Gramm-Überlappung, Regeln `LEK` gegen Exfiltrationsversuche |

Die übrigen Risiken (u.a. Supply Chain, Data and Model Poisoning, Excessive Agency, Unbounded
Consumption) adressiert die Bibliothek nicht oder nur am Rand: Die Tool-Policy kann Folgen
übermässiger Befugnisse eines Agenten begrenzen, ersetzt aber keine Rechtebeschränkung.

Quellen: [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/),
[LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/),
[LLM02:2025 Sensitive Information Disclosure](https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/),
[LLM07:2025 System Prompt Leakage](https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/),
[OWASP LLM Prompt Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html).

## EU AI Act (Verordnung (EU) 2024/1689)

**Art. 15 «Genauigkeit, Robustheit und Cybersicherheit»** gilt für Hochrisiko-KI-Systeme.
Abs. 5 verlangt, soweit angemessen, Massnahmen gegen KI-spezifische Schwachstellen, darunter
Eingaben, die ein Modell zu Fehlern verleiten sollen (adversarial examples, model evasion), und
Vertraulichkeitsangriffe. Prompt-Injection fällt in diese Gruppe.

Die Bibliothek kann eine von mehreren technischen Massnahmen in einem solchen System sein. Sie
erfüllt Art. 15 nicht allein; dazu gehören unter anderem Risikomanagement, Tests, Dokumentation und
Überwachung im Betrieb. Für Systeme ausserhalb der Hochrisiko-Kategorien ist Art. 15 keine Pflicht,
aber eine brauchbare Orientierung. Transparenzpflichten (Art. 50) betreffen andere Fragen
(Kennzeichnung von KI-Interaktion und KI-generierten Inhalten) und werden hier nicht behandelt.

Quelle: [AI Act Service Desk, Art. 15](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-15).

## Schweizer Datenschutzgesetz (revDSG, SR 235.1, in Kraft seit 1. September 2023)

| Artikel | Inhalt | Bezug |
|---|---|---|
| Art. 7 | Datenschutz durch Technik und datenschutzfreundliche Voreinstellungen | Schwärzung von Personendaten in Antworten; Audit standardmässig ohne Klartext |
| Art. 8 | Datensicherheit | technische Massnahme gegen unbefugte Bekanntgabe über das Sprachmodell |
| Art. 9 | Bearbeitung durch Auftragsbearbeiter | Wer einen externen LLM-Judge nutzt, gibt Eingaben an diesen Dienst weiter; ein lokales Modell (z.B. über Ollama) vermeidet das |
| Art. 24 | Meldung von Verletzungen der Datensicherheit | Canary- und Überlappungsbefunde können helfen, einen Abfluss zu bemerken; ob eine Meldepflicht besteht, ist im Einzelfall zu prüfen |

Quellen: [Fedlex, SR 235.1](https://www.fedlex.admin.ch/eli/cc/2022/491/de),
[Bundesamt für Justiz, FAQ zum neuen Datenschutzrecht](https://www.bj.admin.ch/dam/bj/de/data/staat/datenschutz/faq-dsr.pdf.download.pdf/faq-dsr-d.pdf).

## Spotlighting

Hines, K., Lopez, G., Hall, M., Zarfati, F., Zunger, Y., Kiciman, E.: *Defending Against
Indirect Prompt Injection Attacks With Spotlighting.* arXiv:2403.14720, 2024.
[arxiv.org/abs/2403.14720](https://arxiv.org/abs/2403.14720)

Das Paper beschreibt Begrenzer (Delimiting), Datamarking und Encoding und empfiehlt mindestens
Datamarking mit zufälligen Markierungen. `spotlight.py` setzt alle drei Varianten um; die
Begrenzer erhalten hier zusätzlich eine zufällige Kennung je Aufruf.
