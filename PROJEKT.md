# PROJEKT.md — Single Source of Truth

Diese Datei ist der Zustand des Projekts. Jede Sitzung beginnt mit
Lesezugriff auf diese Datei und `git log`. Jeder abgeschlossene Schritt
wird sofort hier eingetragen und/oder committet — bevor mein Kontext
bereinigt wird, nicht danach.

Stand: 2026-10-10

## Ist-Zustand (verifizierbar im Repo)

- v1.2 pushed (`977df82`), Remote `GRADweight/GRADweight.git` (private)
- Repo-Inhalt: README, docs/ (ai-craft, grenzen, referenzen, souverainetaet),
  CONTRIBUTING, CHANGES, LICENSE, guardrails/guard.py, CI-Workflow
- guard.py: 6/6 Selbsttest grün

## Entschieden

- Doku-Struktur v1.x: Marketing-Broschüre → Engineering-Org (v1.1),
  Lachnummer-Prüfung gefixt (v1.2)
- Alle verlinkten Code-Repos sind private (404) — Doku kommuniziert das ehrlich
- Trainings (GRADtrain) bleibt privat — es ist personalisiertes Coaching, kein OSS
- Preise/Kalkulation/Kunden: nie in öffentlichen Doku

## Offene Punkte / ungelöst

- **v1.x:** nur ein Guardrail + Doku — zu dünn, kein Code, kein Angebot
- **v2-Plan (Monorepo G0-G8):** Benutzer unzufrieden, Grund:
  1. "nicht allumfassend" und "überschneidet sich nicht mit dem tatsächlichen Angebot"
  2. "der ursprüngliche Code" soll drin sein, nicht nur Referenzen
  3. Vollständiges Angebot = Governance + Engineering (Training bleibt privat)
  4. Lebenszyklus: starten → umsetzen → wie → abschluss → in betriebnahme
  5. "GitHub-Manier: Ideen und Vorschläge, nicht Marketing-Broschüre"
- **Kontextmanagement:** Benutzer fragt explizit nach Strategie über 1-2 Wochen
  → PROJEKT.md + Git-Log + session_search + MEMORY.md (siehe Protokoll unten)

## Verifizierte Code-Quellen (~/code/gradweight/)

| Ordner | Was dahinter steckt | Status |
|---|---|---|
| `gw-shared-lib/gw_shared_lib/` | rag_core.py, guardrails.py, parsers.py, auth_helpers.py | private Repo `eddavv/gw-shared-lib` |
| `gw-rag-chatbot/code/` | FastAPI-App + Streamlit (Produktrüstung) | private Repo `eddavv/gw-rag-chatbot` |
| `gw-prototypen/shared/src/gw_core/` | **audit.py, authz.py, approval.py, verify.py, tracing.py** — 13 Bausteine, null Abhängigkeiten, echte Tests | uv workspace, CI-ruf |
| `gw-prototypen/autonomy/` | **25 maschinenlesbare JSON-Fälle** (level, governance, ceiling), validiert durch `gradbuild.cli` | machine-readable, Exit 0/1 |
| `gw-prototypen/prototypes/02-rechnungs-extraktion/` | lauffähig + Tests (test_evaluierung.py, test_validate.py) | lauffähig |
| `gradmap/doku/gate-modell.md` | **9 Tore G0-G8** mit K.-o.-Kriterien, RACI, Entscheider | private Repo `GRADweight/gradmap` |
| `gradbuild/doku/architektur.md` | Multi-Agent, RAG, Guardrails, Deploy-Souveränität, Audit | private Repo `GRADweight/gradbuild` |

**Schlussfolgerung:** Die Code-Substanz ist NICHT "Doku + 1 Guardrail" (v1.x)
und auch nicht "8 Gates als Vorlagen" (v2-Plan). Der Kern ist:
`gw_core` (13 Bausteine, null Abhängigkeiten, getestet) + 25 JSON-Fälle mit
Validator + lauffähige Prototypen. Das ist die "Ursprungs-Code", der
im Hub als OSS-Kern leben soll.

## Nächste Schritte (blockiert auf Benutzer-Entscheidung)

- **A (Vollcode):** `gw_core` + 25 JSON-Fälle + Validator → `shared/` im Hub
  als OSS (MIT), CI = Validator + Selftests, 1 lauffähiges Beispiel
  (RAG-Chatbot durch den Lebenszyklus)
- **B (Doku + 1 Modul wie v1.x):** bleibt dünn, wird nicht akzeptiert
- **C (Monorepo wie v2-Plan):** Vorlagen + JSON-Cases, aber ohne `gw_core`
  als OSS-Kern → wieder "nur Doku"
- Warten auf: welche Variante + konkrete Auslassungen am v2-Plan

## Protokoll

| Datum | Schritt | Verifiziert |
|---|---|---|
| 2026-10-10 | v1.1: Hub von Marketing-Broschüre zu Engineering-Org, 8 Doku-Dateien + guard.py | `4dbe4ec` |
| 2026-10-10 | v1.2: Prüfung, 13 Fehler gefixt (fiktive URL, Datum, private Links, DSG-Link) | `977df82` |
| 2026-10-10 | v2-Plan: G0-G8-Lebenszyklus, Monorepo-Struktur, Community-Elemente — im Chat, nicht umgesetzt | Chat |
| 2026-10-10 | PROJEKT.md angelegt: Kontextmanagement-Strategie + verifizierte Code-Quellen + Varianten A/B/C | dieses Commit |

## Sitzungsmatik (verbindlich für alle Folgesitzungen)

1. **Anfang:** `PROJEKT.md` lesen, `git log --oneline -10`, offene Punkte.
   Niemals aus dem Gedächtnis weitermachen.
2. **Während:** Jeder abgeschlossene Schritt wird sofort (im selben Turn)
   hier im Protokoll notiert und/oder committet — vor jeder Kontextbereinigung.
3. **Ende / Blockade / Entscheidung:** Stand, Nächstes, offene Fragen
   aktualisieren, commit mit Datum.
4. **Korrekturen vom Benutzer:** dauerhafte Regel → MEMORY.md;
   wiederkehrender Ablauf → Skill.
5. **Verifikation:** Ergebnis gegen Text prüfen (grep, Lauf, git log),
   nicht gegen Gefühl.
