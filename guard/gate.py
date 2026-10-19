"""`GuardPipeline` — zusammengesetzt aus den 2 Schichten.

```
        user_input
             │
             ▼
  GuardPipeline.run(input)
             │
    ┌────────┴───────────┐
    │                    │
    ▼                    ▼
Signatur-Schicht     Judge (2. Schicht)
(guard.core)         (guard.judge)
    │                    │
    ▼                    ▼
  block?           block?
    │                    │
    ▼                    ▼
   GuardResult(blocked,
               reason,
               categories,
               confidence)
```
"""
from __future__ import annotations

from dataclasses import dataclass

from .core import analyze_prompt_injection, AnalysisResult, InjectionFinding
from .judge import Judge, JudgeResult, DummyJudge


@dataclass(frozen=True)
class GuardResult:
    """Endergebnis der Pipeline.

    `blocked=True` → der Input soll abgewiesen werden.
    `reason` ist das erste (hauptsächlichste) Motiv (Signatur
    oder Judge). `categories` ist die Liste aller
    erkannten Signaturen-Kategorien. `confidence` ist
    der (optionale) Vertrauenswert des Judges.
    """

    blocked: bool
    reason: str
    categories: list[str]
    findings: list[dict]
    confidence: float | None = None

    def to_dict(self) -> dict:
        return {
            "blocked": self.blocked,
            "reason": self.reason,
            "categories": self.categories,
            "findings": self.findings,
        }


class GuardPipeline:
    """Zwei-Schichten-Pipeline: Signatur zuerst, dann Judge.

    **Ordnung:** Die Signatur-Schicht läuft zuerst (deterministisch,
    schnell). Wenn sie blockt, blockt die Pipeline —
    kein zweiter Filter nötig. Wenn sie *nicht* blockt,
    läuft der Judge (fail-closed Default).

    **Offline by default:** `judge=None` → keine zweite
    Schicht, nur Signatur. Für Produktion: `judge=LLMJudge()`.
    """

    def __init__(self, *, judge: Judge | None = None,
                 fail_on_judge_error: bool = True) -> None:
        self.judge = judge or DummyJudge(conservative=fail_on_judge_error)
        self.fail_on_judge_error = fail_on_judge_error

    def run(self, user_input: str) -> GuardResult:
        """Führt alle Schichten durch.

        1. Signatur-Schicht: `analyze_prompt_injection`.
           Wenn `injected` → `blocked=True` (Signatur blockt).
        2. Judge (falls vorhanden): der Judge bekommt
           `upstream_signatures` (= die Signatur-Listen, die
           die Signatur-Schicht erkannt hat).
           Wenn `blocked` → `blocked=True` (Judge blockt).
        3. Sonst → `blocked=False` (pass).
        """
        analysis = analyze_prompt_injection(user_input)
        # Signatur-Block: frühestmöglicher Ausweg
        if analysis.injected:
            sigs = [f.signature for f in analysis.findings]
            return GuardResult(
                blocked=True,
                reason=f"Signatur-Schicht blockt: {analysis.primary_category}",
                categories=analysis.categories,
                findings=[f.to_dict() for f in analysis.findings],
                confidence=1.0,
            )
        # Sonst: Judge-Schicht
        sigs = []  # keine Signatur → leere Liste
        j_result = self.judge.evaluate(user_input, upstream_signatures=sigs)
        return GuardResult(
            blocked=j_result.blocked,
            reason=j_result.reason,
            categories=analysis.categories,  # leer, da kein Signatur
            findings=[],
            confidence=j_result.confidence,
        )

    @property
    def judge_used(self) -> str:
        return type(self.judge).__name__
