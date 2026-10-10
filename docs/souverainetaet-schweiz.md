# Souveränität & Schweizer Kontext

Der Schweizer Kontext ist kein Detail. Die regulatorische Lage bestimmt,
**was technisch möglich ist** — und wo die Grenzen liegen. Diese Doku
sammelt die relevanten Regeln mit **Datum und Quelle**, damit jeder sie
nachprüfen kann — und damit klar ist, **was davon rechtlicher Rat ist und was
Technik**.

> **⚠️ Kein Rechtsrat.** Die obigen Werte sind unser technischer Arbeitszustand
> (Stand: 10/2026). Für verbindliche rechtliche Entscheidungen gilt immer die
> aktuelle Fassung der Verordnung + Ihre Rechtsberatung. **Diese Doku ist
> nicht an die Stelle eines Rechtsberaters.**

---

## EU AI Act — die Fristen, die uns betreffen

**Stand: Digital Omnibus VO (EU) 2026/1744, veröffentlicht 24.07.2026, in Kraft seit 27.07.2026.**
Die Verschiebung ist **final**, nicht mehr vorläufig.

| Pflichten | Was es betrifft | Frist |
|---|---|---|
| **Art. 50** Transparenz/Kennzeichnung, Bestandssysteme | Chatbots, generative Systeme die vor 02.08.2026 in Verkehr | **02.12.2026** |
| **Anhang III** — Hochrisiko | HR, Kreditw., Bildung, Strafverfolg., Migration, Justiz | **02.12.2027** |
| **Anhang I** — Hochrisiko in Produkten | Maschinen, MDR, Fahrzeuge | **02.08.2028** |

**Was sich mit den Verschiebungen NICHT verschoben hat:**
- Verbote (Art. 5)
- AI Literacy (Art. 4)
- GPAI-Pflichten
- **Art. 50(2)** — die Kennzeichnung von AI-generierten Inhalten bleibt
  in der ursprünglichen Fassung (die Verschiebung betrifft bestimmte
  Bestandssysteme, nicht die Grundpflicht)

**Was wir in den Gates G0–G4 dokumentieren:**
- Die Risk-Klassifizierung (minimal / begrenzt / hoch / unannehmbar)
  je System — **vor** dem Build.
- Die Quellen- und Log-Fähigkeiten je Stufe (s.
  [`ai-craft.md`](ai-craft.md), Abschnitt 9).
- Die AI-Literacy-Abdeckung — wer in der Organisation das System
  bedienen darf, muss geschult sein (zahlt auf GRADmap ein).
- Die Watermarking-/Kennzeichnungspflicht je Systemtyp.

---

## DSG / AV — die technische Realität

**Was wir in jedem Auftrag ab Tag 1 dokumentieren:**

| Baustein | Zweck | In welcher Linie |
|---|---|---|
| **AVV** (Auftragsverarbeitungsverpflichtung) | Wer verarbeitet was | GRADmap / GRADbuild G0 |
| **Datenfluss-Doku** | Von wem → an wen, über welchen Pfad | GRADbuild G0 |
| **KI-Register** | Welches System, welche Stufe, welcher Pfad | GRADmap |
| **Pseudonymisierungs-Log** | Wo Daten pseudonymisiert werden | GRADbuild |
| **Access-Level-Metadaten** | Chunk-granulare Zugriffssteuerung | alle (RAG-Kern) |

**Die technische Konsequenz:**

> **Sensible Fragmente gehen nicht in die Cloud.** — diese Entscheidung
> wird in G0 getroffen, nicht «nach dem Build», wenn man merkt, dass
> «der LLM-Dienst doch nicht so wichtig ist».

**Warum das für KMU der Unterschied ist:** eine KMU kann eine Cloud-LLM-Abfrage
für Standard-Queries machen (keine Personen-/Betriebsdaten) und trotzdem
«datenschutzkonform» sein — **weil** der Zugang der sensitiven
Daten **lokal** bleibt. Das ist kein «entweder-oder», es ist ein
**Routing** (s. [`ai-craft.md`](ai-craft.md), Abschnitt 7).

---

## ISO 42001 — die Grundlage

**ISO 42001 (KI-Managementsystem)** ist der internationale Standard
für KI-Risikomanagement. Grundsätzlich:

- **GRADmap** liefert die **Grundlage** — Reifegrad, Richtlinien,
  Verantwortlichkeiten, KI-Register.
- **GRADbuild** liefert die **Umsetzung** — die Gates, die Audit-
  Trails, die dokumentierten Abweichungen.
- **GRADtrain** zahlt auf **Art. 4** (AI Literacy) ein — die geschulte
  Person in der Organisation.

**Was ISO 42001 NICHT ist:** es ist kein «Zertifikat, das man einmal
holt und an die Wand hängt». Es ist ein **System** — mit Policy,
Risiko-Assessment, dokumentierten Entscheidungen und Nachverfolgung.
Unsere Gates sind die **technische Umsetzung** eines solchen Systems.

> **Wichtig:** Wir sind kein ISO-Auditor und keine
> Zertifizierungsstelle. Wir liefern die technische und organisationale
> Grundlage, auf der ein Audit **möglich** wird. Das Audit selbst
> erfolgt über eine zertifizierte Stelle — nicht über uns.

---

## Deployment-Souveränität

**Die Entscheidung, die in G0 getroffen wird:**

| Option | Datenorte | Wann passend |
|---|---|---|
| **On-Prem (M4/GPU)** | lokal im Firmennetz | sensible Fälle, daten-dichte KMU |
| **Exoscale (CH)** | Schweizer Rechenzentrum | Swiss-Cloud, kein On-Prem-Budget |
| **Infomaniak (CH)** | Swiss-Cloud | günstigere Option, standard |
| **Eigener Stack** | Ihr Rechenzentrum | IT-Team vorhanden, volle Kontrolle |
| **Hybrid** | sensible lokal, RAG in CH-Cloud | **meist der richtige Kompromiss** |

**Das Entscheidende ist nicht «welche Cloud», sondern: was ist die
sensitive Grenze.** Diese Grenze wird **vor** der Deployment-Entscheidung
geklärt — nicht danach.

**Warum das eine andere Qualität als «wir hosten in der Schweiz» ist:**
«Swiss hosting» sagt nichts über **was** in der Schweiz bleibt. Uns
geht es um **die Grenze** — und die ist eine technische, nicht eine
Marketing-Entscheidung.

---

## Was wir bewusst NICHT behaupten

- **«Wir sind 100% datenschutzkonform»** — das können wir nicht für
  jeden Kunden, jede Rechtsordnung, jeden Fall garantieren. Wir
  legen die **technische und organisationale Grundlage**, und wir
  dokumentieren die **Grenzen** (s. [`grenzen.md`](grenzen.md)).
- **«Wir sind ISO-42001-zertifiziert»** — wir sind kein Auditor.
  Wir liefern die Grundlage, die ein Audit **möglicher** macht.
- **«Wir hosten alles lokal»** — bei standard Queries ist eine
  Schweizer Cloud-Option (Exoscale, Infomaniak) oft der **bessere**
  Kompromiss, nicht «worse».
- **«KI ersetzt keinen Menschen»** — bei Stufe 3+ (autonom) ist genau
  das der Punkt. Wir bauen Systeme, die **ohne** uns laufen sollen.
  Wenn wir der Flaschenhals bleiben, war das Projekt nicht gut.
