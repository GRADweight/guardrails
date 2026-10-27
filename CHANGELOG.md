# Changelog

Alle wesentlichen Änderungen an diesem Projekt. Format nach
[Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionierung nach
[Semantic Versioning](https://semver.org/lang/de/).

## [2.0.0] – 2026-10-27

Neuaufbau. Die Version 1.x bestand aus einer Liste von 16 englischen Teilstrings und einem
Benchmark, der bekannte Umgehungen als «erwartet: durchlassen» zählte. Diese Version ersetzt sie
vollständig.

### Hinzugefügt

- Paket `gradweight_guardrails` (Distribution `gradweight-guardrails`) mit Typinformationen
  (`py.typed`) und ohne Laufzeitabhängigkeiten.
- Normalisierung: Unicode-NFKD, unsichtbare und Bidi-Zeichen, Doppelgänger, Leetspeak,
  Sperrschrift, Buchstabendreher, zerteilte Wörter, ROT13, Rückwärtstext; Dekodierung von Base64,
  Hex, URL, HTML, Unicode-Escapes und Unicode-Tags mit begrenzter Tiefe.
- Regelfamilien in Deutsch, Französisch, Italienisch und Englisch mit stabilen IDs
  (`docs/regeln.md`), Befunde mit Kategorie, Schweregrad, Sprache und Textstelle.
- Kontextregeln: Erwähnungen in Fragen über Angriffe, Selbstkorrekturen und Entwicklerfragen
  werden nicht blockiert.
- `scan_document()` für indirekte Injection und `spotlight()` (Datamarking, Begrenzer, Base64).
- `scan_tool_input()` mit getrennter Policy für Shell, SQL, URLs und Pfade.
- `OutputGuard` mit Canary-Tokens, System-Prompt-Überlappung, Schweizer Personendaten mit
  Prüfziffern und Entfernung von Bildern auf fremde Hosts.
- `OpenAICompatibleJudge` für Ollama, vLLM, LiteLLM und OpenAI mit strengem JSON-Schema,
  Datamarking, Timeouts, Retries mit Backoff; die Pipeline ist fail-closed.
- Audit-Hook mit Hash statt Klartext.
- Benchmark mit Dev- und Holdout-Set (DE/FR/IT/EN), generiertem Bericht und Regressions-Gate.
- Kommandozeile `python -m gradweight_guardrails scan|bench|rules`.
- CI mit Lint, Typprüfung, Tests auf Python 3.11, 3.13 und 3.14, Paket-Smoke-Test, gitleaks und
  pip-audit.

### Geändert

- Mindestversion Python 3.11 (Python 3.10 hat im Oktober 2026 das Ende der Unterstützung erreicht).

### Entfernt

- Paket `guard` und das Duplikat `guardrails/guard.py`.
- `is_confidential()`, `format_rag_response()` und `DEMO_CHUNKS` (gehörten nicht zur Abwehr).
- Interne Dokumente, die nicht diese Bibliothek beschrieben.

### Migration von 1.x

| 1.x | 2.0 |
|---|---|
| `from guard import detect_prompt_injection` | `from gradweight_guardrails import scan` |
| `detect_prompt_injection(text)` → `bool` | `scan(text).decision` → `Decision.ALLOW/REVIEW/BLOCK`; `scan(text).blocked` |
| `analyze_prompt_injection(text).categories` | `scan(text).findings` (`rule_id`, `category`, `severity`, `language`, `span`) |
| `GuardPipeline(judge=LLMJudge(caller=…))` | `Guard(judge=OpenAICompatibleJudge(base_url, model))` |
| `python -m guard bench` | `python -m gradweight_guardrails bench` |

REVIEW ist neu: Ohne Judge sollte eine Anwendung REVIEW wie BLOCK behandeln oder an einen Menschen
weiterleiten.

## [1.4.0] – 2026-10-19

Signaturliste mit 16 Einträgen, Judge-Schnittstelle als Stub, Benchmark mit 42 Fällen. Ersetzt
durch 2.0.0.
