# CHANGES

Jede **inhaltliche** Änderung in diesem Repo wird hier erfasst —
mit Datum, Doku-Bezug und Quelle. Das ist nicht optional: eine
Engineering-Org, die ihre Doku ändert, ohne es zu notieren,
ist eine Doku, an der niemand mehr glaubt.

**Regel:** jede inhaltliche Änderung (README, Doku, Norm-Frist,
Technik, Grenze) bekommt einen Eintrag hier. Nur äussliche
Korrekturen (Tippfehler, Format) müssen hier **nicht** notiert
werden — aber wenn unsicher, wird es notiert.

**Format:**

```
## YYYY/MM/DD — Kurze Doku-Änderung
- Doku: [README.md](README.md), [docs/ai-craft.md](docs/ai-craft.md)
- Was: [ein Absatz]
- Quelle: [Norm, Code-Referenz, oder konkrete Doku-Stelle]
- Commit: [sha oder Link]
```

---

## 2026/10/15 — Claude-Code-Konfiguration
- `CLAUDE.md`, `.claude/settings.json` (Berechtigungen, Sandbox) und `uv.lock` neu.

---

## 2026/10/19 — v1.4.0: 42 Cases, 16 Signaturen, Judge-Schicht, Regression-Gate

- **Neue Signatur-Familien (v1.4):** 5 neue Signaturen im Kern (11 → 16):
  `you are now dan`, `act as dan` (Jailbreak), `bypass all safety` (Jailbreak),
  `system prompt:` (strukturierte/JSON-Injection), `unfiltered mode` (Jailbreak).
  Alle mit FP-Verifikation gegen die 12 legitmen Cases (0 FP).
- **`guard/judge.py`** (neu): `Judge`-Interface + `DummyJudge` (offline,
  deterministisch, CI-Default) + `LLMJudge` (pluggbar, fail-closed).
- **`guard/gate.py`** (neu): `GuardPipeline` (Signatur-Schicht → Prüfer →
  `GuardResult` mit Kategorie + Grund).
- **`guard/core.py`:** `analyze_prompt_injection()` — kategoriespezifisches Ergebnis
  (statt nur `bool`); `detect_prompt_injection` bleibt rückwärtskompatibel
  (dünner Wrapper über `analyze_`). `INJECTION_CATEGORIES` parallel zu
  `INJECTION_SIGNATURES`, mit `assert len(...) == len(...)` zur Zeitkomplexität-Gleichheit.
- **`tests/test_standalone_sync.py`** (neu): erzwingt Signatur- und
  Conf-Liste-Gleichheit zwischen Standalone `guardrails/guard.py` und
  Paketkern (schließt bekannte Lücke aus CLAUDE.md `12.10`).
- **`tests/test_bench_regression.py`** (neu): Per-Kategorie FP/FN-
  Regression-Gate gegen `guard/bench_data/guard-bench-baseline.json`.
  **Negativ-Beweis** in `scripts/negative-gate-test.py`: injiziert
  temporär einen FP, zeigt dass der Gate Exit-1 liefert, revertiert.
- **Bench:** 32 → **42 Cases** (+5 block +4 pass +1 adv mit Unicode-
  Steuerzeichen — alle verifiziert per `scripts/verify-new-cases.py`).
- **51 Tests, alle grün** (47 → 51, +3 Sync + 1 Regression).
- `guard/__init__.py`: `1.3.0` → `1.4.0`, neue Exports.
- `pyproject.toml`: version `1.4.0`.
- `scripts/`: 3 neue Skripte (`verify-new-signatures.py`,
  `verify-new-cases.py`, `negative-gate-test.py`, `scan-version-strings.py`).

**Zustand 19.10, verifiziert:** `pytest tests` → 51/51 (0.02 s).
`python -m guard bench --metrics` → 42/42, FP=0 FN=0, Regression: OK.
Negativ-Gate-Test: PASS (Exit 1 bei FP-Inektion).

---

## 2026/10/12 — v1.3.0: Guard wird zum lauffähigen Paket mit Guard-Bench

- `guard/` (neu): Python-Paket — `guard/core.py` (die drei Kernfunktionen,
  konstante Listen exports), `guard/bench.py` (Bench-CLI), `guard/__main__.py`
  (`python -m guard bench` | `python -m guard "<text>"` | `--version`).
- `guard/bench_data/guard-bench.json` (neu): **32 dokumentierte Cases** in
  4 Kategorien (`legit` 12, `inj` 10, `adv` 5, `edge` 5). Jeder Case mit
  Begründung. **Die Grenzen sind Teil des Nachweises**: Base64,
  Whitespace-Aufweitung und Zeilenumbruch entkommen dem Zeichenfolgen-Filter
  — als `adv-01, adv-02, adv-03` mit `expect: pass` dokumentiert.
  Verifiziert: 32/32 deterministisch (Py 3.11, 12.10).
- `tests/` (neu): 47 pytest-Tests
  (`test_guard_core.py` 39 + `test_guard_bench.py` 8). Alle grün in 0.02 s.
- `pyproject.toml` (neu): `gradweight-guardrails` v1.3.0, `requires-python
  >=3.8`, **null externe Abhängigkeiten**, `.[dev]` = pytest.
- `QUICKSTART.md` (neu): 5-Zeilen-Quickstart (Standalone + Paket + Bench + Test).
- `README.md`: Guard-Bench-Abschnitt neu, Quickstart-Verweis, 32/47/Ci-Zahlen.
- `.github/workflows/guard-selftest.yml`: CI auf Py 3.9/3.11/3.12
  (Standalone + Install + Bench + pytest + Einzel-CLI).
- `guardrails/guard.py`: bleibt lauffähig (Legacy-Modus).
- `LICENSE`: korrekte Beschreibung (bisher: Copy-Paste der `internal-kb`-Lizenz —
  PPTX/DOCX-Referenz hier unzutreffend). Alle Rechte vorbehalten +
  Referenz-/Attribution-Ausnahme + Community-PR-Regel.
- `PROJEKT.md`: entfernt (internes Sitzungs-Management; gehört in `internal-kb`).
- `CHANGES.md`: Eintrag v1.3.0.

**Zustand 12.10, verifiziert:** `python3 -m guard bench` → 32/32 grün
(Exit 0). `pytest tests` → 47/47 grün (0.02 s).

---

## 2026/10/10 — Prüfung und Korrekturen (v1.2)

- `guardrails/guard.py` (neu): lauffähiger Guardrails-Baustein mit
  deterministischem Selbsttest — `python3 guardrails/guard.py`.
  Erste lauffähige Artefakt im Hub (verifiziert: alle 6 Checks grün).
- `.github/workflows/guard-selftest.yml` (neu): GitHub-Actions-Workflow,
  der den Selbsttest bei jedem Push/PR auf `guardrails/` laufen lässt.
  Kein Netzwerk, keine Installation.
- Korrekturen:
  - `referenzen.md` neu geschrieben: falsch erdichtete Quellen entfernt
    (KI-MIG, kaputte Pfade, falsche Org-Zuordnung), Prototyp-Katalog-Zahl
    auf 26 Angebote + 2 implementierte Prototypen korrigiert, Verweis auf
    laufende Bausteine hier im Repo ergänzt.
  - Digital Omnibus: «in Kraft seit 24.07.2026» -> «veröffentlicht
    24.07.2026, in Kraft seit 27.07.2026» (README, Doku, CHANGES).
  - `souverainetaet-schweiz.md`: Grossschreibung Zeile 3 korrigiert.
  - `LICENSE`: Ausnahmen- und Community-Sektion ergänzt (guard.py als
    Referenz-Baustein, Doku-Beiträge via PR).
  - `README.md`: Selbsttest-Befehl und Verweis auf laufende Bausteine.
- Was noch fehlt (bewusst dokumentiert):
  - Mehr lauffähige Bausteine hier im Repo (RAG-Kern, Prompt-Basis,
    Evals) — aktuell nur Verweis auf `gw-shared-lib`, das ausserhalb
    dieser Org liegt.
  - Repository `internal-kb` (intern) nicht in `referenzen.md` verlinkt
    (bewusst: kein interner Link in der öffentlichen Doku).

## 2026/10/10 — Hub von Marketing-Broschüre zu Engineering-Org

- Doku: `README.md` (komplett neu), `docs/ai-craft.md` (neu),
  `docs/souverainetaet-schweiz.md` (neu), `docs/grenzen.md` (neu),
  `docs/referenzen.md` (neu), `CONTRIBUTING.md` (neu), `CHANGES.md` (neu)
- Was:
  - README: von 4 Adjektiven («datenschutzkonform, dokumentiert, ohne
    Vendor-Lock-in») zu einer technischen Engineering-Org mit inline-echtem
    Code, Request-Pfad, den Künsten und der Nachhaltigkeit.
  - `docs/ai-craft.md` — 9 konkrete Techniken (RAG vs. FT,
    Prompt als Code, Guardrails, Konfidenz-Routing, Multi-Agent,
    Evals, Inferenz-Routing, Deployment, Audit) — jede mit
    Entscheidung + Mechanik + Grenze.
  - Souveränität: `docs/souverainetaet-schweiz.md` — EU AI Act
    (Digital Omnibus VO (EU) 2026/1744, in Kraft seit 27.07.2026;
    Anhang III → 02.12.2027, Anhang I → 02.08.2028), DSG/AV,
    ISO 42001, Deployment-Souveränität — **mit Datum und Quelle**.
  - Grenzen: `docs/grenzen.md` — was die Praxis **nicht** macht.
    (Kein 100 % datenschutz, kein ISO-Auditor, kein Hosting, kein
    «alles behaupten»)
  - Referenzen: `docs/referenzen.md` — die Behauptung → Artefakt-Karte.
    (RAG-Kern in `gw-shared-lib`, Guardrails in `guardrails.py`,
    20 PoC im Prototyp-Katalog)
  - Community: `CONTRIBUTING.md` — Issue zuerst, PR-Regeln, Stile,
    keine verbotene Begriffe («KI-Magie», «wir sind die besten»,
    «KI-Plattform», «98 % Zufriedenheit»).
- Quelle:
  - Digital Omnibus VO (EU) 2026/1744 (EUR-Lex), in Kraft seit 27.07.2026
  - `gw-shared-lib/{rag_core,guardrails,parsers}.py` (Org `eddavv`)
  - `engineering/doku/architektur.md` (Org)
  - `ai-prototypen-katalog.md` (Kanon: `internal-kb`, privat)
- Commit: `d51f0ed` (v1.0, Hub-Grundgerüst) → **dieser Commit** (v1.1, Engineering-Org)
- Hinweis: **Keine Kunden, keine Preise, keine internen Zahlen** in
  diesem Repo. (Regel aus der `LICENSE`: Alle Rechte vorbehalten.)
