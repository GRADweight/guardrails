# GRADweight — KI Engineering, das im Alltag arbeitet

Solo-Konsultanz für den Schweizer Mittelstand. Wir bauen, messen und verankern KI-Lösungen, die in Ihrer Hand bleiben und in Ihrem Rahmen laufen: datenschutzkonform, dokumentiert, ohne Vendor-Lock-in.

**Drei Services. Ein System.** Jede Linie ist ein eigenständiges Repo mit eigenem Fokus, eigener Doku, eigenem Delivery-Standard. Zusammen ergeben sie einen durchgängigen Pfad: Ihre Leute können es, Ihre Organisation trägt es, Ihr System läuft.

<!-- ============== DIE DREI SERVICES (Kurzfassung) ============== -->

| Service | Was er löst | Wer davon profitiert | Repo |
|---|---|---|---|
| **GRADtrain** · AI Training | Ihre Leute nutzen KI souverän: L1 Foundation, L2 Strategie, L3 Orchestration | Ganze Belegschaft, Führung, Engineering | [github.com/GRADweight/gradtrain](https://github.com/GRADweight/gradtrain) |
| **GRADmap** · AI Governance | Reifegrad messen, Richtlinien, Gates G0–G8, Verantwortlichkeiten, KI-Richtlinie | GL, Fachbereich, IT, Compliance | [github.com/GRADweight/gradmap](https://github.com/GRADweight/gradmap) |
| **GRADbuild** · AI Engineering | Prozess-Schritte in Stufen automatisieren: ab 70 % (S2) bis 90 % autonom (S3) | Fachbereich, IT, GL | [github.com/GRADweight/gradbuild](https://github.com/GRADweight/gradbuild) |

**Ein Satz je Service:**

- **GRADtrain** — Menschen souverän machen: drei Stufen, solo, auf Ihren Kontext. Keine Massen-Events, keine Folien-Ablagerung.
- **GRADmap** — Regeln messbar machen: Reifegrad, Guidelines, Gates, Verantwortung. Keine Gutachten, die im Akt verschwinden.
- **GRADbuild** — Prozess-Schritte automatisieren: Stufen 1 bis 4, Gates G0–G4, Code & Deployment, Abnahme auf Zahlen.

<!-- ============== EIN SYSTEM (Wie die drei zusammenhängen) ============== -->

```
 GRADtrain            GRADmap              GRADbuild
 ┌────────────┐      ┌────────────┐       ┌────────────┐
 │ L1  sicher │ ──►  │ Reifegrad  │ ──►   │ Stufe 1    │
 │ L2  Roadmap│      │ Richtlinie │       │ Stufe 2    │
 │ L3  Bau    │ ◄──  │ Gates G0–G8│ ◄──   │ Stufe 3    │
 └────────────┘      └────────────┘       └────────────┘
   Können               Rahmen               Betrieb
```

- **Reihenfolge, die wir empfehlen:** GRADtrain (Kompetenz) → GRADmap (Rahmen) → GRADbuild (Betrieb). Jeder der drei kann auch allein gestartet werden. Wir empfehlen, die Reihenfolge zu wählen, die dem aktuellen Engpass am meisten entgegengesetzt ist.
- **Was jede Linie nicht ist:** GRADtrain macht keine Beratung, GRADmap baut kein System, GRADbuild schreibt keine Strategie. Das ist bewusst getrennt, damit jeder Bereich in sich sauber ist.
- **Was sie gemeinsam haben:** Doku in DSG-Kontext, Schweizer Hand, alle Vorlagen verbleiben Ihnen — keine Tool-Abhängigkeit.

<!-- ============== SCHWEIZER KONTEXT — STANDARD ============== -->

Die Schweiz ist kein Detail. Die regulatorische Lage bestimmt, was technisch möglich ist. Vier Punkte, die bei jedem Auftrag Teil der Agenda sind:

| Bereich | Was wir liefern | Standard |
|---|---|---|
| **DSG · AV** | AVV ab Tag 1, Datenfluss-Doku, Pseudonymisierungs-Log, KI-Register | Teil des G0-Gates in GRADbuild |
| **EU AI Act** | Art. 50 Kennzeichnung, Art. 4 KI-Kompetenz (zahlt auf GRADmap ein), Art. 26 Haftung bei Hochrisiko | Teil von GRADmap |
| **Deployment** | On-Prem, Exoscale, Infomaniak, oder Ihr Stack — Entscheidung in G0, nicht nachher | GRADbuild + GRADmap |
| **Lokale Modelle** | Ollama (Llama/Mistral/Qwen) für sensible Fälle, Cloud-LLMs für Standardfälle, Konfidenz-Routing je Fall | Alle drei Services |
| **ISO 42001** | GRADmap liefert die Grundlage; GRADbuild liefert die Umsetzung; GRADtrain zahlt auf Art. 4 ein | Alle drei |

<!-- ============== METHODIK =========…==== -->

| Prinzip | Was es bedeutet |
|---|---|
| **Prozess vor Produkt** | Wir automatisieren Schritt X Ihres Prozesses — nicht «irgendwas mit KI». |
| **Zahlen vor Code** | Abnahmekriterien stehen vor dem Build. Wenn die Zahl nicht erreicht wird, ist der Build nicht fertig. |
| **Sichtbare Gates** | G0–G4 (Engineering), G0–G8 (Governance). Jedes Gate öffnet nur, wenn die Antwort dokumentiert ist. |
| **Code ist versioniert** | Alles im Repository: Code, Prompts, Konfiguration, Evals, Runbooks. Nichts geht verloren, wenn ein Gerät oder eine Person weg ist. |
| **Übergabe statt Abhängigkeit** | Das Ziel ist der Moment, in dem Sie das System ohne uns betreiben können. |

<!-- ============== WIE SIE KONTAKT AUFNEHMEN ============= -->

**Kontakt:** [gradweight.ch](mailto:gradweight.ch) · [gradweight.ch](https://gradweight.ch)

**Typische Anfrage:** «Wir hätten gern einen 30-minütigen Termin, um einzuschätzen, ob GRADbuild für uns sinnvoll ist — und wenn ja, ab welcher Stufe wir starten.»

**Was das Ergebnis ist:** ein konkreter Vorschlag, in welche Linie (train/map/build) der erste Schritt passt, und eine kurze Einschätzung mit Abnahmekriterien. Kein Pitch, kein Skript.

<!-- ============== ORG-NAV ============= -->

| Repo | Fokus |
|---|---|
| [github.com/GRADweight](https://github.com/GRADweight) | Diese Seite — der Hub |
| [github.com/GRADweight/gradtrain](https://github.com/GRADweight/gradtrain) | **Training** · L1/L2/L3 |
| [github.com/GRADweight/gradmap](https://github.com/GRADweight/gradmap) | **Governance** · Reifegrad · Richtlinie |
| [github.com/GRADweight/gradbuild](https://github.com/GRADweight/gradbuild) | **Engineering** · Stufen · Gates |
| [github.com/GRADweight/biz](https://github.com/GRADweight/biz) | Interne Doku (Katalog, Protokolle, Vorlagen) — **nicht öffentlich lesbar** |
