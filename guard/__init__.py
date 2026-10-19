"""GRADweight Guardrails — Python-Paket.

Lauffähiger Referenz-Baustein: erste Schutzschicht vor dem LLM-Anruf.

Was dieses Paket KANN (bewusst klein, deterministisch, ohne Netz):
  - bekannte Prompt-Injection-Signaturen erkennen (Erstfilter, kategoriebasiert)
  - Retrieval-Chunks mit Vertraulichkeits-Metadaten kennzeichnen
  - eine quell-zitierte Antwort bauen; ehrliche Nicht-Antwort bei Leerergebnis
  - Guard-Bench: dokumentiertes, wiederholbares Testkorpus (42 Cases)
  - Zweite Schicht: pluggbarer LLM-Prüfer (Judge) + GuardPipeline, fail-closed

Was dieses Paket NICHT kann (bewusst dokumentiert, s. README):
  - semantische Injection-Varianten (z. B. Base64-verpackte Signaturen),
    die eine Zeichenfolge-Signatur umschiffen
  - keine Rechts-, Datenschutz- oder Risikobeurteilung — das ist Aufgabe
    der Doku (docs/souverainetaet-schweiz.md), nicht des Codes

Zwei Schichten: `guard.core` (Signatur, deterministisch) + `guard.judge`
(Prüfer, pluggbar), komponiert in `guard.gate.GuardPipeline`. Für
Produktion: zusätzlich ein LLM-basierter Prüfer oder ein spezialisiertes
Moderationsmodell als zweite Schicht.
"""
from __future__ import annotations

from .core import (
    DEMO_CHUNKS,
    INJECTION_SIGNATURES,
    INJECTION_CATEGORIES,
    CONFIDENTIAL_LEVELS,
    detect_prompt_injection,
    analyze_prompt_injection,
    InjectionFinding,
    AnalysisResult,
    is_confidential,
    format_rag_response,
)
from .bench import (
    BENCH_FILE,
    load_bench,
    run_bench,
    bench_summary,
)
from .judge import Judge, DummyJudge, LLMJudge, JudgeResult
from .gate import GuardPipeline, GuardResult

__version__ = "1.4.0"
__all__ = [
    "DEMO_CHUNKS",
    "INJECTION_SIGNATURES",
    "INJECTION_CATEGORIES",
    "CONFIDENTIAL_LEVELS",
    "detect_prompt_injection",
    "analyze_prompt_injection",
    "InjectionFinding",
    "AnalysisResult",
    "is_confidential",
    "format_rag_response",
    "BENCH_FILE",
    "load_bench",
    "run_bench",
    "bench_summary",
    "Judge",
    "DummyJudge",
    "LLMJudge",
    "JudgeResult",
    "GuardPipeline",
    "GuardResult",
    "__version__",
]
