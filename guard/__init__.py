"""GRADweight Guardrails — Python-Paket.

Lauffähiger Referenz-Baustein: erste Schutzschicht vor dem LLM-Anruf.

Was dieses Paket KANN (bewusst klein, deterministisch, ohne Netz):
  - bekannte Prompt-Injection-Signaturen erkennen (Erstfilter)
  - Retrieval-Chunks mit Vertraulichkeits-Metadaten kennzeichnen
  - eine quell-zitierte Antwort bauen; ehrliche Nicht-Antwort bei Leerergebnis
  - Guard-Bench: dokumentiertes, wiederholbares Testkorpus (24 Cases)

Was dieses Paket NICHT kann (bewusst dokumentiert, s. README):
  - semantische Injection-Varianten (z. B. Base64-verpackte Signaturen),
    die eine Zeichenfolge-Signatur umschiffen
  - keine Rechts-, Datenschutz- oder Risikobeurteilung — das ist Aufgabe
    der Doku (docs/souverainetaet-schweiz.md), nicht des Codes

In Produktion: zusätzlich ein LLM-basiertes Guardrail oder ein
spezialisiertes Moderationsmodell VOR diesen Filter schalten.
"""
from __future__ import annotations

from .core import (
    DEMO_CHUNKS,
    INJECTION_SIGNATURES,
    CONFIDENTIAL_LEVELS,
    detect_prompt_injection,
    is_confidential,
    format_rag_response,
)
from .bench import (
    BENCH_FILE,
    load_bench,
    run_bench,
    bench_summary,
)

__version__ = "1.3.0"
__all__ = [
    "DEMO_CHUNKS",
    "INJECTION_SIGNATURES",
    "CONFIDENTIAL_LEVELS",
    "detect_prompt_injection",
    "is_confidential",
    "format_rag_response",
    "BENCH_FILE",
    "load_bench",
    "run_bench",
    "bench_summary",
    "__version__",
]
