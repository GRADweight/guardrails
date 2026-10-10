# Referenzen — wo die Behauptung aufhört und der Code anfängt

Dieses Repo ist der **Hub** — die Behauptungen in der README und in den
Docs sind **alle** auf concrete Artefakte verweisbar. Diese Doku ist die
Karte, die die Behauptung mit dem Artefakt verknüpft.

> **Ehrensache:** wenn eine Behauptung in einem der hier verlinkten
> Repos **nicht** nachvollziehbar ist, dann ist die Behauptung im Hub
> **falsch** — und sie gehört raus. Das ist der Punkt.

---

## Implemented Bausteine (GRADweight-Organisation)

| Baustein | Was es ist | Wo |
|---|---|---|
| **RAG-Kern** | Chunking, Embeddings, Qdrant, Retrieval, Antwort mit Quellenangabe | `gw-shared-lib/gw_shared_lib/rag_core.py` |
| **Dokument-Parser** | PDF (pdfplumber), Word (python-docx), optionales OCR | `gw-shared-lib/gw_shared_lib/parsers.py` |
| **Guardrails** | Injection-Filter, Vertraulichkeits-Filter, Antwortformat | `gw-shared-lib/gw_shared_lib/guardrails.py` |
| **Auth-Helfer** | MSAL, Token-Handling, Microsoft-Id | `gw-shared-lib/gw_shared_lib/auth_helpers.py` |
| **RAG-Chatbot** (Produkt #1) | FastAPI + Streamlit, RAG-Frag-Chat über interne Doku | `gw-rag-chatbot/code/app.py` |
| **Prototyp-Katalog** | 20 PoC mit technischer Umsetzung und Abnahmekriterien | [`~/Documents/…/ai-prototypen-katalog.md`](../ai-prototypen-katalog.md) |

> **Zugang:** die Repos sind in der **GRADweight-Organisation** auf GitHub.
> Wenn ein Repo für Sie nicht lesbar ist (PRIVATE), fragen Sie — das ist
> eine organisatorische, keine technische Entscheidung.

---

## Normen & Standards

| Standard | Bezug | Status |
|---|---|---|
| **EU AI Act** (VO (EU) 2024/1689) | Risikoklassifizierung, Art. 50, Anhang I/III | in Kraft; Digital Omnibus (VO (EU) 2026/1744) hat die Fristen final verschoben (Anhang III → 02.12.2027, Anhang I → 02.08.2028) |
| **DSG / AV** (CH) | Datenfluss, AVV, KI-Register | je Auftrag ab Tag 1 |
| **ISO 42001** | KI-Managementsystem | GRADmap liefert die Grundlage, GRADbuild die Umsetzung |

> **Quellen: ** [EU-AI-Act-Service-Desk](https://ai-act-service-desk.ec.europa.eu/de/ai-act/annex-3),
> [EUR-Lex VO (EU) 2026/1744](https://eur-lex.europa.eu/eli/reg/2026/1744),
> [KI-MIG CH §2](https://www.fedex.admin.ch/de/kimd.html) (Stand 10/2026).

---

## Techniken (Künste)

Jede Technik in [`ai-craft.md`](ai-craft.md) ist in den implementierten
Bausteinen **nachvollziehbar**:

| Technik | In welchem Baustein |
|---|---|
| RAG vs. Fine-Tuning | `rag_core.py` (RAG), `ai-craft.md` §1 (Entscheidung) |
| Prompt-Engineering als Code | `rag_core.py` (System-Prompt), `ai-craft.md` §2 |
| Guardrails (mehrere Schichten) | `guardrails.py`, `ai-craft.md` §3 |
| Konfidenz-Routing | `gradbuild/doku/architektur.md`, `ai-craft.md` §4 |
| Multi-Agent mit Protokoll | `gradbuild/doku/architektur.md`, `ai-craft.md` §5 |
| Evals als Regressionsnetz | `ai-craft.md` §6 (je System: `evals/`) |
| Souveränes Inferenz-Routing | `ai-craft.md` §7 |
| Deployment-Souveränität | `gradbuild/doku/architektur.md`, `souverainetaet-schweiz.md` |
| Audit & Erklärbarkeit | `gradbuild/doku/architektur.md`, `ai-craft.md` §9 |

> **Warum das eine andere Qualität als «wir nutzen RAG» ist:**
> jede Technik ist **auf einen konkreten Baustein** zurückerklärenbar.
> Wenn Sie in einem der implementierten Repos eine Technik finden,
> die hier behauptet wird, aber nicht so implementiert ist — dann
> ist hier ein Fehler. Das ist der Unterschied zu einer
> Marketing-Broschüre.

---

## Was diese Doku NICHT ist

- **Keine Kundenliste.** Wir nennen keine Kunden (Datenschutz, Vertrag,
  Vertraulichkeit).
- **Keine Metrik-Sammlung.** «200+ Projekte», «98 % Zufriedenheit» —
  keine dieser Zahlen steht hier. Wir meinen **den Code**, nicht die Zahl.
- **Kein Preisverzeichnis.** Preise, Kalkulation, Marge — steht hier nicht.
  Das ist intern, und «intern» ist bewusst.
- **Kein «Seit 2015» / «Leading**». Wir sind eine Solo-Praxis.
  Das sagt auch die `LICENSE` aus: **Alle Rechte vorbehalten.**
  Wir behaupten nichts über Marktanteil, was wir nicht zeigen können.

---

## Wie man verifiziert (das ist der ehrliche Teil)

Wenn Sie eine Behauptung hier lesen, die Sie nicht kaufen:

1. **Finden Sie** den verweisenden Baustein (Tabelle oben).
2. **Lesen Sie** den Code (in der GRADweight-Organisation auf GitHub).
3. **Vergleichen** Sie: was hier behauptet wird, was dort implementiert ist.
4. **Fehler?** Issue eröffnen. Nicht auf Twitter, nicht im Mail —
   das hier ist die richtige Stelle.

**Das ist die Community-Stelle, die dieses Repo sein soll.**
Nicht «wir sind die besten», sondern «lesen Sie die Doku, finden Sie
den Code, und sagen Sie uns, wo wir unrecht haben».
