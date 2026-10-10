# Wie hier gearbeitet wird

Dieses Repo ist eine **öffentliche Engineering-Org** — nicht eine
Marketing-Broschüre, die «wir machen KI» behauptet, und auch nicht
eine Closed-Source-Box. Es ist die Stelle, an der Technik, Standards
und die drei Linien (train/map/build) zusammenlaufen.

> **Tonalität:** wir schreiben wie wir arbeiten — konkret, mit
> Quellen, mit Grenzen. Kein «wir sind die besten», kein Adjektiv-Futter.
> Wenn Sie einen PR einbringen, der «KI-Magie» behauptet, ohne zu zeigen,
> **was** gemeint ist, wird der PR nicht gemerged. Das ist kein Tonfall,
> das ist eine Qualitätsgrenze.

---

## Was hier willkommen ist

| Art | Beispiel |
|---|---|
| **Doku-Korrektur** | Eine Norm-Frist ist veraltet (Digital-Omnibus hat sie verschoben) → PR mit neuer Frist + Quelle |
| **Technik-Ergänzung** | Eine Technik, die wir deployen, ist hier nicht dokumentiert → Issue zuerst, dann PR |
| **Gate-Entscheidung** | Eine G0–G4-Entscheidung, die besser/dokumentierter beschrieben werden kann |
| **Referenz** | Ein implementierter Baustein ist hier verlinkt, aber der Link ist kaputt |
| **Souveränitäts-Kontext** | Eine neue CH-Datenfluss-Erfordernis, die in `souverainetaet-schweiz.md` fehlt |

**Was hier NICHT willkommen ist:**
- Rebranding- / «Modernisierung»-PRs («lassen Sie uns das in React umschreiben»)
- UI-Verbesserungen, die den Inhalt nicht verbessern
- «KI-Sprite»-UIs, die die Architektur verbergen
- Requests, die eine Behauptung entfernen, die wir **zeigen** sollten

---

## Prozess

### 1. Issue zuerst
- Jede inhaltliche Änderung braucht ein **Issue** mit:
  - **Was** (welche Doku/Doku-Teil)
  - **Warum** (welche Technik fehlt, welche Norm veraltet, welche Grenze unklar)
  - **Quellen** (Norm, Code-Referenz, oder konkrete Doku-Stelle)
- Wir antworten, bevor ein PR gemerged wird. **Kein PR ohne vorheriges Issue.**

### 2. PR-Regeln
- **Ein PR = eine Sache.** Kein «Doku-Update + README-Redesign».
- **Grenzen bleiben in der Doku.** Wenn Sie eine Technik entfernen,
  entfernen Sie die verweisende Behauptung (nicht nur die Technik).
- **Normen-Fristen mit Datum und Quelle.** «02.12.2027 (VO (EU) 2026/1744,
  in Kraft seit 24.07.2026)」 — nicht «kurz bevor 2027».
- **Keine Preise, keine Kunden, keine internen Zahlen.** Diese Repo ist
  **öffentlich lesbar** — alles, was hier steht, ist für alle lesbar.

### 3. Merge-Kriterien
- Die Doku ist **technisch korrekt** (oder verweist auf die richtige Doku).
- Die Grenzen sind **nicht verschmolzen** (s. `grenzen.md`).
- Der Ton passt zur Praxis (konkret, mit Quellen, keine Adjektive).
- Bei Normen: die **Quelle** ist verlinkt (nicht aus dem Gedächtnis).

---

## Stile

### Sprache
- **Deutsch** für alle Doku und README (die Praxis spricht Deutsch).
- **Englisch** ist okay für Code-Kommentare und technische Begriffe
  (RAG, Chunking, Guardrail).
- **Kein «wir sind die besten»** — das ist keine Stilregel, das ist
  eine Qualitätsgrenze.

### Struktur
- **Tabellen > Listen** (wenn es eine klare Dimension gibt).
- **Code-Blocks** für Techniken (nicht nur Beschreibung).
- **Quellen** bei jeder Norm oder jeder Zahl.
- **Grenzen** in jeder Doku (nicht in einem Anhang, den niemand liest).

### Verbotene Begriffe (bewusst)
- «KI-Magie» / «AI-Sprite»
- «wir sind die besten / führend / #1 in der Schweiz»
- «98 % Zufriedenheit / 200+ Projekte» (keine Behauptung, die wir nicht zeigen)
- «KI-Plattform» (wir bauen Systeme, nicht Plattformen)
- «wir automatisieren alles» (wir automatisieren Prozess-Schritte, in Stufen)

---

## Wie man «das hier ist falsch» sagt

**Das ist der ehrliche Teil, den wir suchen:**

1. Öffnen Sie ein **Issue** in diesem Repo (nicht im Mail, nicht auf Twitter).
2. Beschreiben Sie:
   - **Was** Sie gefunden haben (eine Behauptung, die nicht nachvollziehbar ist)
   - **Wo** (Doku, Doku-Teil, oder Doku-Behauptung)
   - **Warum** Sie es falsch finden (mit Quelle, wenn möglich)
3. Wir antworten. Wenn es stimmt: **Doku wird korrigiert, Commit wird
   geschrieben, Sie kommen im `CHANGES.md` vor.**

**Das ist der Prozess, der eine Engineering-Praxis von einer
Marketing-Broschüre trennt. Er funktioniert nur, wenn beide Seiten
ihn ernst nehmen.**

---

## Wenn Sie einen implementierten Baustein finden, der hier nicht
dokumentiert ist

Das ist **der** häufigste Fall, und es ist **kein** Zeichen von
Respektlosigkeit — es ist der Punkt. Hier ist der Prozess:

1. **Issue** öffnen: «Technik im Baustein `gw-shared-lib/…` oder
   `gw-rag-chatbot/…`, die hier nicht dokumentiert ist».
2. **Beschreiben Sie** die Technik (ein Absatz, kein Essay).
3. **Verlinken Sie** den Baustein (Repo, Path, oder Line).
4. **Wir** entscheiden: wird die Technik in die Doku aufgenommen
   (mit Korrektur), bleibt sie (mit Begründung), oder wird sie
   entfernt (mit Begründung).
5. **Commit** + `CHANGES.md`-Eintrag.

**Das ist der ehrliche Prozess, den eine Engineering-Praxis braucht,
um eine Engineering-Praxis zu bleiben.**
