# Referenzen — Behauptung und Artefakt, ehrlich getrennt

Die Doku in diesem Repo behauptet Dinge über eine Technik. Behauptung
und Artefakt sind getrennt, damit klar ist, was Sie **hIER** sehen und
was Sie **ANDERSWO** (in einem Org-Repo) sehen müssen, um zu
verifizieren.

> **Stand: 10/2026.** Die verknüpften Bausteine in den drei
> Service-Linien- und den implementierten Hilfs-Repos sind
> **ORG-NUR** (private). Sie sind sichtbar für Mitglieder der
> GRADweight-Org auf GitHub — nicht für jeden, der auf einen Link
> klickt. Wenn Sie den Code hinter dieser Doku sehen und
> verifizieren wollen: **Org-Zugang** nötig.
>
> Die Doku selbst (README, docs/, guardrails/) ist die
> **öffentliche** Hälfte — und sie ist vollständig hier im Repo.
> Das ist der ehrliche Punkt: **die Doku ist verifizierbar,
> der Code hinter ihr ist verifizierbar, wenn Sie Zugang haben.**

---

## Was in diesem Repo liegt (verifizierbar für alle Besucher)

| Artefakt | Was es ist | Wo |
|---|---|---|
| **Guardrails-Baustein** (lauffähig) | Injection-Filter, Vertraulichkeits-Filter, quell-zitierte Antwortformate, inkl. Selbsttest | [`guardrails/guard.py`](guardrails/guard.py) — `python3 guardrails/guard.py` |
| **CI-Workflow** für den Selbsttest | Läuft bei jedem Push/PR auf `guardrails/`, kein Netzwerk | [`.github/workflows/guard-selftest.yml`](.github/workflows/guard-selftest.yml) |
| **Doku: die Künste** | 9 Techniken je mit Entscheidung + Mechanik + Grenze | [`docs/ai-craft.md`](docs/ai-craft.md) |
| **Doku: Schweizer Kontext** | AI Act (Digital Omnibus), DSG/AV, ISO 42001, Deployment | [`docs/souverainetaet-schweiz.md`](docs/souverainetaet-schweiz.md) |
| **Doku: Grenzen** | was die Praxis nicht macht | [`docs/grenzen.md`](docs/grenzen.md) |
| **Doku: Normen-Fristen** | mit Datum und Quelle | [`docs/souverainetaet-schweiz.md`](docs/souverainetaet-schweiz.md) |
| **Community-Rahmen** | wie man beiträgt, was hier gesucht ist | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| **Doku-Nachverfolgung** | jede inhaltliche Änderung | [`CHANGES.md`](CHANGES.md) |

**Was das heisst:** jeder Besucher dieses Repos kann die Doku lesen,
den Guardrails-Code ausführen, und die Behauptungen in der Doku
gegen die implementierte Version in `guardrails/guard.py`
**in diesem Repo** prüfen.

---

## Was in den Org-Repos liegt (verifizierbar mit Org-Zugang)

Diese Referenzen sind **privat** für Außenstehende; sie sind für
Organisation-Mitglieder der GRADweight-Org auf GitHub sichtbar.
Wenn Sie den Code hinter einer Doku-Behauptung sehen wollen:
**Org-Zugang** ist die Voraussetzung.

| Baustein | Was es ist | Ort (GRADweight-Org) |
|---|---|---|
| **RAG-Kern** | Chunking, Embeddings, Qdrant, Retrieval, Antwort mit Quellenangabe | `gw-shared-lib → gw_shared_lib/rag_core.py` |
| **Dokument-Parser** | PDF (pdfplumber), Word (python-docx), optionales OCR | `gw-shared-lib → gw_shared_lib/parsers.py` |
| **Guardrails (LangChain-Kontext)** | gleiche Logik wie hier + Retrieval-Framework | `gw-shared-lib → gw_shared_lib/guardrails.py` |
| **Auth-Helfer** | MSAL, Token-Handling, Microsoft-Identitäten | `gw-shared-lib → gw_shared_lib/auth_helpers.py` |
| **RAG-Chatbot** (Produkt 1) | FastAPI + Streamlit über interne Dokumente | `gw-rag-chatbot → code/app.py` |
| **Angebots-Katalog** | 26 Angebots-Doks (PoC 01–26); **2** davon als Prototyp implementiert (`01-rag-chatbot`, `02-rechnungs-extraktion`), die übrigen als Angebots-Dokumentation | `gw-prototypen → docs/`, `prototypes/` |
| **Architektur-Prinzipien** (Service-Linie) | Multi-Agent, RAG, Deployment-Souveränität, Audit-Trail | `engineering → doku/architektur.md` |
| **Gate-Modell** (Goverance) | Gates G0–G8 | `governance → doku/gate-modell.md` |
| **Stufen-Modell** (Engineering) | Stufe 1–4 (Assistent → Autonom) | `engineering → doku/stufen.md` |

> **Ehrlicher Unterschied:** «26 Prototypen» ist die **Botschaft**,
> die der Katalog trägt. Tatsächlich implementiert: 2 (RAG-Chatbot,
> Rechnungs-Extraktion). Angebots-Dokumentationen mit technischer
> Umsetzung: 24. Wir machen den Unterschied hier, weil die Summe der
> Bezeichnung «Prototypen-Katalog» ihn sonst verschleiern würde —
> und weil wir keine Lachnummer sein wollen, indem wir «26
> Prototypen» behaupten, von denen 24 keine Code-Dateien sind.

---

## Normen und Standards

| Standard | Bezug | Status |
|---|---|---|
| **EU AI Act** (VO (EU) 2024/1689) | Risikoklassifizierung, Art. 50, Anhang I/III | in Kraft; Digital Omnibus (VO (EU) 2026/1744, veröffentlicht 24.07.2026, in Kraft seit 27.07.2026) hat die Hochrisiko-Fristen final verschoben (Anhang III → 02.12.2027, Anhang I → 02.08.2028) |
| **DSG (CH)** | [Bundesgesetz über den Datenschutz](https://www.fedlex.admin.ch/eli/cc/61/804900) (SR 235.1) | je Auftrag ab Tag 1 |
| **ISO 42001** | KI-Managementsystem | GRADmap liefert die Grundlage, GRADbuild die Umsetzung |

> **Quellen:**
> [AI-Act Service Desk, Anhang III](https://ai-act-service-desk.ec.europa.eu/de/ai-act/annex-3),
> [VO (EU) 2026/1744 (Digital Omnibus), EUR-Lex](https://eur-lex.europa.eu/eli/reg/2026/1744).
>
> Wenn eine Frist hier veraltet ist: das ist **kein** Vertrauensbruch,
> es ist ein Fehler — und er gehört in ein Issue
> (s. [`CONTRIBUTING.md`](CONTRIBUTING.md)). Die Fristen werden mit
> Datum gepflegt, damit so etwas auffällt.

---

## Techniken (Künste) — verknüpft mit Artefakten

Jede Technik in [`ai-craft.md`](ai-craft.md) ist auf einen konkreten Ort
zurückverweisbar:

| Technik | Artefakt | Zugang |
|---|---|---|
| Guardrails (mehrere Schichten) | [`guardrails/guard.py`](guardrails/guard.py) **hier** + `gw-shared-lib/guardrails.py` | alle / Org |
| RAG mit Quellenangabe | `gw-shared-lib/rag_core.py`, [`ai-craft.md`](ai-craft.md) §1 | Org |
| Prompt-Engineering als Code | `gw-shared-lib/rag_core.py`, [`ai-craft.md`](ai-craft.md) §2 | Org |
| Konfidenz-Routing | `engineering/doku/architektur.md`, [`ai-craft.md`](ai-craft.md) §4 | Org |
| Multi-Agent mit Protokoll | `engineering/doku/architektur.md`, [`ai-craft.md`](ai-craft.md) §5 | Org |
| Evals als Regressionsnetz | [`ai-craft.md`](ai-craft.md) §6 (je System: `evals/`) | Doku / Org |
| Souveränes Inferenz-Routing | [`ai-craft.md`](ai-craft.md) §7, `souverainetaet-schweiz.md` | Doku |
| Deployment-Souveränität | `engineering/doku/architektur.md`, `souverainetaet-schweiz.md` | Org / Doku |
| Audit und Erklärbarkeit | `engineering/doku/architektur.md`, [`ai-craft.md`](ai-craft.md) §9 | Org / Doku |

---

## Wie man das hier verifiziert

1. **Doku-Behauptung** hier im Repo: lesen, prüfen, Issue wenn Fehler.
2. **Guardrails-Code**: `python3 guardrails/guard.py` — der Selbsttest
   läuft ohne Netzwerk, ohne Installation.
3. **Code hinter einer Doku-Behauptung** (RAG-Kern, Prompt-Basis,
   Evals-Set, Multi-Agent): **Org-Zugang** nötig, weil die
   Referenz-Repos private sind. Das ist eine bewusste Organisations-
   Entscheidung, keine technische Grenze.

---

## Was diese Doku NICHT ist

- **Keine Kundenliste.** Wir nennen keine Kunden (Datenschutz, Vertrag,
  Vertraulichkeit).
- **Keine Metrik-Sammlung.** «200+ Projekte», «98 % Zufriedenheit» —
  keine dieser Zahlen steht hier. Wir meinen **den Code**, nicht die Zahl.
- **Kein Preisverzeichnis.** Preise, Kalkulation, Marge — steht hier
  nicht. Das ist intern, und «intern» ist bewusst.
- **Kein «Seit 2015» / «Leading».** Wir sind eine Solo-Praxis, und das
  sagt auch die `LICENSE` aus: **Alle Rechte vorbehalten.** Wir
  behaupten nichts über Marktanteil, was wir nicht zeigen.
- **Kein «verifizierbar» mit Anführungszeichen.** Wenn ein Artefakt
  private ist, schreiben wir es. Nicht «lesen Sie den Code, er ist
  irgendwo da» — sondern «lesen Sie den Code, er ist in
  `gw-shared-lib`, das ist Org-nur».