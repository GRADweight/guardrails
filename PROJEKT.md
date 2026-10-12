# PROJEKT.md — Single Source of Truth (gradweight-hub)

Diese Datei ist der Zustand des Projekts. Jede neue Sitzung beginnt mit
dem Lesen dieser Datei + `git log` + `git status`. Ergebnis: Einschätzung
an Edin (Ist-Zustand, offene Punkte, nächste 3 Schritte, Risiken).
Jeder abgeschlossene Schritt wird SOFORT hier notiert und/oder committet,
bevor Kontextbereinigung passieren kann.

Stand: 2026-10-10 · Remote: `GRADweight/GRADweight` (private) · main = `73b9e40`+

---

## 1 · Roter Faden (verbindend, vom Benutzer entschieden 2026-10-10)

**Das Vorgehen im Hub wird über die Automatisierungsstufen aus dem
eigenen AI-Engineering-Inhalt strukturiert — gradBuild-Grad 01–05:**

```
Grad 01  Assistent   Modell schlägt vor, Mensch voll kontrolliert (full_control)
Grad 02  Copilot     Freigabe je Aktion (per_action) — Approval-Queue + Audit-Trail
Grad 03  Workflow    Freigabe je Gate / Feste Kette (per_gate, fixed_chain) — + KPI (GB-07)
Grad 04  Agent       Mandat mit systemseitigen Limiten, Rollback, Schattenbetrieb, Messung
Grad 05  Multi-Agent Orchestrierung, Mandat pro Rolle, Sampling-Audit, Kill-Switch
```

**Gilt für ALLE Aspekte, von Plan bis Inbetriebnahme:** Jedes Dokument und
jeder Code-Pfad des Hubs ist *je Grad* ausgeschrieben:
- Plan (G0/G1): welche Anforderungen steigen je Grad? (Verbots-Check, Risiko, Rollen)
- Umsetzen (G2–G3): welche Bausteine, welche Evals, welche Tests je Grad?
- Wie (Code): `gw_core`-Bausteine je Grad (siehe §3) + gradBuild-Regeln GB-01…16
- Abschluss (G4): Kill-Kriterien je Grad (Grad 4+: Shadow-Test GB-13, KPI)
- Inbetriebnahme (G5–G8): Rollout, Betrieb, Rollback, Ausserbetriebnahme je Grad

**Harte Grenzen (gilt immer, Quelle: `docs/26-autonomie-mappe.md`):**
- Rule of Two (GB-03): Grad ≥ 4 → eine von drei (fremde Eingaben /
  sensible Daten / Aussenwirkung) muss strukturell weg sein.
- Schutzfunktionen (GB-06): max. Grad 3, nie in der Kette.
- Money-Effects (GB-09): Grad ≥ 4 → systemseitige Limiten (ERP/Bexio), nie im Prompt.

**Quellen (alle verifiziert auf disk, 2026-10-10):**
- `~/code/gradweight/gw-prototypen/docs/26-autonomie-mappe.md` — Grad 0–5,
  IST/ZIEL je Prototyp, 8 fehlende Bausteine, GB-Regeln, Nicht-verkaufen-Liste
- `~/code/gradweight/gw-prototypen/shared/src/gw_core/` — 13 Bausteine
  (approval, audit, verify, authz, tracing, bexio, …), null Abhängigkeiten, ~40 Tests
- `~/code/gradweight/gw-prototypen/autonomy/01.json…25.json` + `grad-engineering`-Validator (CI)
- `~/code/gradweight/gw-shared-lib/gw_shared_lib/` — rag_core, guardrails, parsers, auth
- `~/code/grad-governance/doku/gate-modell.md` — Tore G0–G8
- `~/code/grad-engineering/doku/architektur.md` — Multi-Agent, RAG, Guardrails, Deploy

## 2 · Scope (Entscheidung 2026-10-10)

- **DRIN:** AI Governance + AI Engineering, über ALLE Automatisierungsgrade 01–05,
  Plan bis Inbetriebnahme. Training bewusst RAUS (personalisiertes Coaching, privat).
- **AI Governance als eigenes Modul:** «Unternehmen KI-governance-sicher machen» —
  auch mit technischen Mitteln: Policy-as-Code, Rollen/AuthZ, Audit-Trail,
  Injection-/PPI-Testing, Register, Validator (Grad-Deckel je Anwendung),
  KPI/Messung, Rollback/Kill-Switch. Nicht nur XLSX-Vorlagen.
- **Original-Code gehört IN den Hub** (als OSS-Kern `shared/`), nicht nur verlinkt.
  Alle verlinkten Repos sind private (404) — das ist kein Zustand, den man verteidigt.

## 3 · Die 8 Bausteine (aus der Autonomie-Mappe, alle implementiert + getestet)

| Baustein | gw_core | Hebt |
|---|---|---|
| Approval-Queue (Freigabe/Anpassen/Zurückstellen, Rechte-Check) | `approval.py` (12 Tests) | Grad 1 → 2 |
| Audit-Trail (append-only, wer/was/wann, CSV) | `audit.py` (4 Tests) | Grad 1 → 2 |
| Zweitmodell-Prüfung (Zahlen/Zitate, VETO) | `verify.py` (5 Tests) | Grad 1 → 2 |
| Golden-Set-Scorer (Feld-Genauigkeit + CLI) | `beleg_extraktion.evaluierung` (8 Tests) | Abnahme je Grad |
| KPI-Report (Adoption-Rate, Gummistempel-Prävention) | `api.py:kpi()` (GB-07) | Grad 2 → 3 |
| AuthZ-Policy (Rolle × Prototyp, admin, VETO im Audit) | `authz.py` (6 Tests, GB-08) | je Grad |
| Tracing (LLM-Request-Protokoll, GB-11) | `tracing.py` (2 Tests) | je Grad |
| Bexio-Adapter (systemseitige Limiten, Dry-Run, GB-09) | `bexio.py` (3 Tests) | Grad 3 → 4 |

## 4 · Arbeits- und Sitzungsprotokoll (verbindend)

**Branch-Modell (Entscheidung 2026-10-10):**
- Arbeit erfolgt auf Branches `feature/<thema>` / `doku/<thema>`.
- **immer Lieferung an `main`** (Squash-Merge), main = always green (CI).
- main ist der Kontextanker: PROJEKT.md + Doku + Code auf main = aktueller Stand.

**Sitzungsstart (jede neue Session):**
1. `PROJEKT.md` lesen, `git log --oneline -10`, `git status`, CI-Status.
2. Einschätzung an Edin: Ist-Zustand, Offene Punkte, nächste 3 Schritte, Risiken.
3. Nie aus dem Gedächtnis — nur aus Repo + Memory + Session-Datenbank.

**Während der Sitzung:** Jeder abgeschlossene Schritt SOFORT in §6 Protokoll
+ Commit (klein, deutsch, mit Beleg). Nicht anhäufen.

**Sitzungsende / Blockade / Entscheidung:** §1–§5 bei Bedarf aktualisieren,
Commit + Push auf main (oder PR, falls Branch), dann Einschätzung-Update.

**Dauerhaftes:** Korrektur von Edin → MEMORY.md; wiederkehrender Ablauf → Skill.

## 5 · Offene Punkte / Entscheide

- [ ] Lizenz für OSS-Kern (`shared/`): MIT? (aktuell LICENSE = Alle Rechte)
- [ ] `gw_core` + autonomy-JSONs + grad-engineering-Validator als `shared/` in den Hub kopieren
      (oder Org-Repo `GRADweight/gw-shared`?) — Edin entscheidet Org-Namen
- [ ] Repo public: ja/nein, wann (voraussetzungen: LICENSE, Security-Scan, Issues/CoC)
- [ ] Bexio-Sandbox-Tokens für den Beispiel-Durchlauf (fremde Secrets — nie committen)
- [ ] Golden-Set #02: 30–50 echte CH-Belege nötig (Platzhalter heute)
- [ ] Approval-Queue in #01 RAG einbinden (Baustein steht, 1 Tag)
- [ ] .github/ISSUE_TEMPLATE + CODE_OF_CONDUCT + SECURITY + CI (Validator + Selftests)

## 6 · Protokoll

| Datum | Schritt | Verifiziert |
|---|---|---|
| 2026-10-10 | v1.1 Hub-Neuaufbau (8 Doku-Dateien + guard.py) | `4dbe4ec` |
| 2026-10-10 | v1.2 Lachnummer-Prüfung (13 Fehler gefixt) | `977df82` |
| 2026-10-10 | v2-Plan G0–G8 Monorepo (Chat, verworfen): nicht allumfassend, kein Original-Code | Chat |
| 2026-10-10 | PROJEKT.md v1: Sitzungs-Matik + verifizierte Code-Quellen | `73b9e40` |
| 2026-10-10 | **Entscheidung Edin:** Roter Faden = Automatisierungsgrad 01–05 (Assistent→Multi-Agent) für alle Aspekte Plan→Inbetriebnahme; Branches→main immer; Sitzungsstart mit Einschätzung; AI-Governance-Modul mit technischen Mitteln | dieses Commit |
| 2026-10-10 | Autonomie-Mappe + gw_core + 8 Bausteine verifiziert und als Grundlage erfasst (§1, §3) | 26-autonomie-mappe.md + gw_core Tests |

## 7 · Nächste Schritte (Reihenfolge)

1. Edin: Lizenz-Entscheid (MIT?) + Org-Namen für den OSS-Kern.
2. OSS-Kern in den Hub: `shared/` (gw_core + autonomy-JSONs + grad-engineering-Validator +
   Tests) + `examples/` (Rechnungs-Extraktion #02, der einzige Vollgrad-Beleg) + CI.
3. Doku je Grad umschreiben: `plan.md`, `umsetzen.md`, `wie.md`, `abschluss.md`,
   `inbetriebnahme.md` — jede mit Grad-Spalte 01–05 + GB-Regeln + Baustein-Verweis.
4. AI-Governance-Modul: «Unternehmen sicher machen» — Technical-Controls (AuthZ,
   Audit, Injection-Tests, Grad-Deckel-Validator, Kill-Switch) + Governance-Kontrollen
   (Richtlinie, Register, Rollen, KPI) — als eigenes Verzeichnis mit lauffähigen Checks.
5. Community: ISSUE_TEMPLATE, CODE_OF_CONDUCT, SECURITY, CI-Status, Topics.
6. Release: Security-Scan (Preise/Secrets/Kunden), LICENSE, dann public (bei Ja).
