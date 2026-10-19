# grad-guardrails — Guard-Baustein + technische Fundament-Doku von GRADweight

Der Guardrails-Baustein **lauffähig** — und die Fundament-Doku der Praxis
(Souveränität, Normen, Grenzen, Künste) daneben. Wir sind eine
Engineering-Praxis für KI-Systeme im Schweizer Mittelstand.
Der Unterschied ist nicht das Versprechen — es ist, **was wir zeigen**.
Jede Aussage in diesem Repo verweist auf eine konkrete Technik, ein
konkretes Bauteil oder eine konkrete Norm. Nicht auf Adjektive.

> **Statt** «datenschutzkonform, dokumentiert, ohne Vendor-Lock-in»
>(das sagt jeder):
> **So** — ein RAG-Pfad mit Access-Level-Metadaten pro Chunk, ein
> Prompt-Injection-Filter, der vor dem LLM läuft, ein
> Konfidenz-Routing, das unter einem Schwellwert an einen Menschen gibt,
> und eine Deployment-Entscheidung, die in einem dokumentierten Gate
> getroffen wird, nicht nach dem Build.

Das ist der Kern. Drei Service-Linien — jede ein eigenes Repo mit eigener
Doku — und darunter ein gemeinsames technisches Fundament.

---

## Die Praxis in drei Linien

| Linie | Was sie liefert | Technische Substanz | Repo |
|---|---|---|---|
| **GRADtrain** — Menschen | KI-Kompetenz L1→L2→L3 statt Folien-Ablagerung | Praxisaufbau, Kontext-Aufgaben, Orchestrierung eigener Modelle | [grad-training](https://github.com/GRADweight/grad-training) (Org) |
| **GRADmap** — Organisation | Reifegrad, Richtlinie, Gates | Messbare Kriterien, dokumentierte Abweichung, KI-Register | [grad-governance](https://github.com/GRADweight/grad-governance) (Org) |
| **GRADbuild** — System | Prozess-Schritte automatisieren (Stufe 1→4) | Multi-Agent, RAG, Guardrails, Audit-Trail, Deployment | [grad-engineering](https://github.com/GRADweight/grad-engineering) (Org) |

> **Stand 10/2026:** Die drei Service-Linien-Repos sind heute Org-nur.
> **Entscheidung (12.10):** sie werden am **25.10.2026** öffentlich —
> danach gilt: die Links oben sind für alle aufrufbar. Bis dahin:
> nur für Org-Mitglieder.

Reihenfolge, die wir empfehlen: `train` → `map` → `build`. Jede Linie
funktioniert allein; die Reihenfolge folgt dem Engpass, nicht der Logik
eines Katalogs.

```
 GRADtrain              GRADmap               GRADbuild
 ┌────────────┐        ┌────────────┐        ┌────────────┐
 │ L1 sicher  │  ────► │  Reifegrad │  ────► │  Stufe 1   │
 │ L2 Roadmap │   ◄─── │  Richtlinie│   ◄─── │  Stufe 2   │
 │ L3 Orchest.│        │  Gates G0–G8│       │  Stufe 3/4 │
 └────────────┘        └────────────┘        └────────────┘
   Können                 Rahmen               Betrieb
```

---

## Das technische Fundament (das ist der eigentliche Punkt)

Unter den drei Linien läuft ein gemeinsamer Stack. Er ist bewusst
**narrow, versioniert und austauschbar** — kein Framework-Fetisch, keine
«AI-Plattform», die niemand versteht.

**Kernbestandteile** (implementiert, nicht Behauptung):

| Baustein | Was es konkret tut |
|---|---|
| **RAG-Kern** | Chunking → Embeddings → Vektorstore → Retrieval → Antwort **mit Quellenangabe**. Chunk-granulare `access_level`-Metadaten für Multi-Tenant. |
| **Dokument-Parser** | PDF (`pdfplumber`), Word (`python-docx`); OCR als optionales Extra. |
| **Guardrails** | Prompt-Injection-Prüfung **vor** dem LLM-Aufruf; Vertraulichkeits-Filter auf Retrieval-Ergebnissen; saubere quell-zitierte Antwortformate. |
| **Auth-Helfer** | u. a. MSAL für Microsoft-Identitäten (in CH-KMU Standard). |
| **Inferenz** | Cloud-LLMs für Standardfälle, **lokale Modelle via Ollama** für sensible Fälle — Entscheidung je Auftrag, nicht Dogma. |
| **Deployment** | On-Prem (M4/GPU), Exoscale, Infomaniak oder Ihr Stack. In einem Gate entschieden, nicht improvisiert. |

### Ein konkreter Guardrail-Baustein (so arbeiten wir)

Der komplette Baustein ist in diesem Repo lauffähig — als Paket
(`guard/`) und als Standalone-Datei (`guardrails/guard.py`):

```bash
python3 -m guard bench                 # Guard-Bench: 42 dokumentierte Cases
python3 -m guard "<eigener Input>"     # Einzelprüfung
python3 guardrails/guard.py            # Standalone-Selbsttest (keine Installation)
```

**Guard-Bench** (`guard/bench_data/guard-bench.json`) ist kein Selbstlob —
es ist ein wiederholbares Korpus von 42 Cases in vier Kategorien
(`legit`, `inj`, `adv`, `edge`). Jeder Case trägt eine `note` mit der
Begründung des erwarteten Verhaltens. **Die Grenzen sind Teil des
Nachweises:** Base64-verpackte Injections, Whitespace-Aufweitung und
Zeilenumbrüche entkommen dem Zeichenfolgen-Filter — das steht im Corpus
als `adv-01…03` (Plus `adv-06` Unicode) mit `expect: pass`. Das ist kein
Zufall, sondern der geprüfte Zustand; die Abdeckung liegt in der
LLM-Guard-Schicht (dann: `guard/bench.py` als Contract, LLM-Guard als
Implementierung).

```python
# guard/core.py — erster Filter, läuft VOR dem LLM
INJECTION_SIGNATURES = (
    "ignore all previous instructions",
    "you are now in developer mode",
    "reveal the system prompt",
    "show me the database connection string",
    "drop table ",
    "curl http://",
)

def detect_prompt_injection(user_input: str) -> bool:
    low = user_input.lower()
    return any(sig in low for sig in INJECTION_SIGNATURES)
```

Bewusst simpel und **erweiterbar** — für Produktion schalten wir zusätzlich
ein LLM-basiertes Guardrail davor. Wir verstecken keine Grenzen: was ein
Signatur-Listfilter kann und was nicht, zeigt die Guard-Bench —
die komplette Liste mit Kategorien, Cases und Grenzen in
[`guard/bench_data/guard-bench.json`](guard/bench_data/guard-bench.json),
technische Tiefe in [`docs/ai-craft.md`](docs/ai-craft.md).

### Zwei Schichten — Signatur und Prüfer

`guard/core.py` ist die **Signatur-Schicht** (deterministisch, null Netz,
null externe Abhängigkeit — läuft in jedem Kramkasten). Semantische
Varianten entkommen (dokumentiert: `adv-01…06`). Für diese liegt die
**zweite Schicht**:

- `guard/judge.py` — der `Judge`: ein pluggbares Prüf-Interface.
  `DummyJudge` (Offline-Default, deterministisch, für CI/Tests),
  `LLMJudge` (eigene Implementierung für Produktion, z. B. via
  `openai` oder `anthropic`). **Fail-closed**: bei Fehler blockt der
  Prüfer, nicht *durchlässt*.
- `guard/gate.py` — `GuardPipeline`, die beide Schichten komponiert:
  Signatur-Schicht → Prüfer → `GuardResult` mit Kategorie + Grund.

```python
from guard import GuardPipeline, LLMJudge
# Für Produktion: echter LLM-Caller
pipe = GuardPipeline(judge=LLMJudge(caller=my_llm_caller))
res = pipe.run(user_input)
if res.blocked:
    # Signatur oder Prüfer hat blockiert — res.reason + res.categories
    ...
```

Die **Signatur-Schicht bleibt die Basis**: schnell, deterministisch,
keine Abhängigkeit. Die zweite Schicht ergänzt das, was der Filter
nicht kann — ohne den Filter zu verstecken. Die Guard-Bench mit
Regression-Snapshot (`guard/bench_data/guard-bench-baseline.json`
+ `tests/test_bench_regression.py`) blockt jeden PR, der ein
False-Positive auf legitmen Cases erzeugt — ein beweisbarer Gate
(s. `scripts/negative-gate-test.py`, der den Gate fälschlich triggert).

### Der Request-Pfad in einem System

```
   Anfrage
     │
     ▼
┌─────────────┐   ja    ┌──────────────────┐
│ Injection-  │────────►│ block/entwürfen  │
│ Schutz      │         └──────────────────┘
└─────┬───────┘
      │ nein
      ▼
┌─────────────┐   kein Treffer  ┌────────────────┐
│ Retrieval   │────────────────►│ "ich weiss     │
│ + Access-   │   (Conf. < θ)   │  es nicht"     │
│ Filter      │                 └────────────────┘
└─────┬───────┘
      │ gefunden
      ▼
┌─────────────┐   vertraulich? ┌───────────────┐
│ Antwort mit │────────────────►│ Reduzierung / │
│ Quellenangabe│                 │ Freigabe      │
└─────┬───────┘                 └───────────────┘
      ▼
 Audit-Trail (Zeitstempel, Input/Output, Freigabender)
```

Jede Antwort **entweder mit Quellenangabe oder als Nicht-Antwort**. Das ist
kein Nice-to-have — es ist die Grundregel, die uns unterscheidet.

---

## Die Künste — was «KI-Engineering» hier heisst

Nicht «irgendwas mit KI», sondern ein Satz konkreter, trainierter
Fähigkeiten. Ausgewählte (vollständig in [`docs/ai-craft.md`](docs/ai-craft.md)):

- **RAG vs. Fine-Tuning** — wann was, und warum KMU fast immer RAG +
  Kontext zuerst, Fine-Tuning nur bei wiederholtem, dominierendem Muster.
- **Prompt-Engineering als Code** — versioniert, getestet, mit
  Abnahmekriterien, nicht als Fingerspitzengefühl.
- **Konfidenz-Routing** — unter θ → Mensch, über θ → autonom; der Schwellwert
  wird je Auftrag kalibriert und dokumentiert.
- **Evals als Regressionsnetz** — bei jedem Modell-Update voller Testlauf;
  keine Modelle, die man «einmal» getestet hat.
- **Multi-Agent mit Protokoll** — spezialisierte Agenten, die sich per
  Ergebnis-Protokoll weiterreichen statt einem Big-Ball-of-Mud.
- **Souveränes Inferenz-Routing** — Cloud vs. On-Prem je Sensitivität,
  dokumentiert je Fall.
- **Audit & Erklärbarkeit** — jede KI-Aktion: wann, was, warum, wer freigab.

---

## Nachhaltigkeit — was «dauerhaft» bei uns heisst

Dauerhaft ist hier **kein Marketingwort**. Es hat drei konkrete Sinnen:

1. **Austauschbarkeit** — der Stack ist versioniert und austauschbar.
   Wenn ein Modell, ein Vektorstore oder ein Parser ausgetauscht wird,
   ändert sich die Doku, nicht Ihr Vertragsverhältnis. Kein Lock-in.
2. **Normen statt Tricks** — GRADmap liefert die Grundlage für
   **ISO 42001** (KI-Managementsysteme); die Gates machen die
   Abweichung messbar; das KI-Register wird geführt.
3. **Repos bleiben Sie-nützlich** — Code, Prompts, Konfiguration, Evals und
   Runbooks sind im Repository. Wenn ein Gerät oder eine Person weg ist,
   bleibt das System. Das Ziel ist der Moment, in dem Sie es **ohne uns**
   betreiben können.

---

## Schweizer Kontext (das ist kein Detail)

Die regulatorische Lage bestimmt, was technisch möglich ist. Stand der
Fakten — **verifiziert, nicht aus dem Gedächtnis**:

| Regel | Inhalt | Stand (verifiziert 10/2026) |
|---|---|---|
| **DSG / AV** | AVV ab Tag 1, Datenfluss-Doku, KI-Register | Basis bei jedem Auftrag |
| **EU AI Act · Anhang III** | Hochrisiko-Pflichten (u. a. HR, Kredit, Bildung) | ab **02.12.2027** |
| **EU AI Act · Anhang I** | Hochrisiko in Produkten (Maschinen, MDR) | ab **02.08.2028** |
| **EU AI Act · Art. 50** | Transparenz/Kennzeichnung (Bestandssysteme) | Übergangsfrist bis **02.12.2026** |
| **Digital Omnibus** | VO (EU) 2026/1744, in Kraft seit 27.07.2026 | Termine **final** |
| **ISO 42001** | KI-Managementsystem — GRADmap liefert die Grundlage | aufbaubar in jeder Linie |

> ⚠️ **Kein Rechtsrat.** Die obigen Werte sind unser technischer Arbeitszustand.
> Für verbindliche rechtliche Entscheidungen gilt immer die aktuelle Fassung
> der Verordnung + Ihre Rechtsberatung. Fristen ändern sich — wir referenzieren
> sie im [`docs/souverainetaet-schweiz.md`](docs/souverainetaet-schweiz.md) mit
> Datum, damit jeder sie gegenprüfen kann.

---

## Was das hier NICHT ist

Bewusst, damit niemand es falsch versteht:

- **Keine «KI-Plattform»**, die alles behauptet und nichts zeigt.
- **Kein Framework-Fetisch** — kein «wir nutzen X» ohne Grund.
- **Kein Rechts- oder Steuerberater** — wir liefern die technische und
  organisationale Grundlage, nicht die Rechtsansicht.
- **Kein Black-Box-Service** — jede Behauptung in diesem Repo ist
  durchverweisbar (Doku, Code, oder Norm).

---

## Für die GitHub-Community

Dieses Repo ist der **technische Anker** — die Stelle, an der Technik,
Standards und die drei Linien zusammenlaufen. Dafür ist es gebaut:

- 🔍 **Lesen:** Architekturentscheidungen und die Künste direkt im Markdown.
- 💬 **Mitdenken:** Issues sind willkommen — ob eine Technik zu robust ist,
  ob eine Norm besser passt, ob ein Gateway fehlt.
- 🤝 **Beitragen:** siehe [`CONTRIBUTING.md`](CONTRIBUTING.md) — wie man
  Doku korrigiert, eine Technik ergänzt oder eine Norm aktualisiert, ohne
  den Ton zu verlieren.
- 🔗 **Umsetzen:** die implementierten Bausteine in den
  [Gradweight-Repos](docs/referenzen.md) — realer Code, keine Mocks.

**Was wir ausdrücklich nicht suchen:** Rebrandings, «AI-Sprite»-UIs,
oder die Forderung, es müsse jetzt «ein Chatbot wie X». Wir bauen
KMU-Systeme, die nach zwei Jahren noch laufen — das hat Priorität.

**Und wir zeigen es:** `python3 -m guard bench` läuft in diesem Repo —
**42 dokumentierte Guard-Bench-Cases** (erkannt / entkommt / dokumentierte
Grenze), dazu 51 pytest-Tests im [`tests/`-Ordner](tests/) und eine CI
über Python 3.9/3.11/3.12. Mehr lauffähige Bausteine folgen, je Linie.

---

## Navigation

| Repo | Fokus |
|---|---|
| [github.com/GRADweight/grad-training](https://github.com/GRADweight/grad-training) | **Train** — KI-Kompetenz L1/L2/L3 |
| [github.com/GRADweight/grad-governance](https://github.com/GRADweight/grad-governance) | **Map** — Reifegrad, Richtlinie, Gates |
| [github.com/GRADweight/grad-engineering](https://github.com/GRADweight/grad-engineering) | **Build** — Automatisierung in Stufen |
| → implementierte Bausteine | [`docs/referenzen.md`](docs/referenzen.md) |
| → vollständige Normen-Fristen | [`docs/souverainetaet-schweiz.md`](docs/souverainetaet-schweiz.md) |
| → die Künste (Technik) | [`docs/ai-craft.md`](docs/ai-craft.md) |
| → wo wir bewusst aufhören | [`docs/grenzen.md`](docs/grenzen.md) |

**Kontakt:** [edin@gradweight.ch](mailto:edin@gradweight.ch) · [gradweight.ch](https://gradweight.ch)

**Typische Anfrage:** «Wir hätten gern einen 30-minütigen Termin, um
einzuschätzen, ob `build` für uns sinnvoll ist — und wenn ja, ab welcher
Stufe wir starten.» Ergebnis: ein konkreter Vorschlag mit
Abnahmekriterien. Kein Pitch, kein Skript.
