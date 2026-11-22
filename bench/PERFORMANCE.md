# Performance der Regelschicht

Diese Datei wird von `scripts/perf.py` erzeugt. Die Werte hängen vom Rechner ab und
werden deshalb nicht in CI geprüft, nur ihr Vorhandensein und ihre Übereinstimmung mit
der README.

Methode: Alle Texte aus `bench/data` (dev und holdout) werden in 20 Durchläufen in jeweils zufälliger Reihenfolge geprüft; gemessen wird
jeder einzelne Aufruf mit `time.perf_counter_ns()`. Kein LLM-Judge, kein Netz, keine
künstlichen Wartezeiten. Die Laufzeit eines LLM-Judges kommt bei Bedarf hinzu und hängt
vom Modell und der Infrastruktur ab; sie ist hier nicht gemessen.

Gemessen am 2026-10-27 mit `scripts/perf.py`, Version 2.0.0, Python 3.13.17, Intel(R) Xeon(R) Processor @ 2.80GHz, ein Thread, Systemlast beim Start 2.46 (1 min) / 1.22 (5 min) bei 2 Kernen. Durchsatz über alle Benchmark-Texte: 1260 Aufrufe/s; einmaliges Kompilieren der Muster: 165 ms.

| Messung | Aufrufe | p50 | p95 | p99 |
|---|---:|---:|---:|---:|
| Benchmark-Texte, Chat | 5800 | 0.52 ms | 2.17 ms | 5.46 ms |
| Benchmark-Texte, Dokument | 2100 | 0.66 ms | 4.33 ms | 6.27 ms |
| Benchmark, Tool-Eingaben | 880 | 0.10 ms | 0.22 ms | 2.15 ms |
| Geschäftstext 1 000 Zeichen | 20 | 3.5 ms | 7.4 ms | 7.4 ms |
| Geschäftstext 10 000 Zeichen | 20 | 49.0 ms | 75.2 ms | 82.8 ms |
| Geschäftstext 50 000 Zeichen (Obergrenze) | 20 | 160.1 ms | 223.8 ms | 258.7 ms |
