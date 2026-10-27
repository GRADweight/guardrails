"""Pipeline: Regelschicht → (optional) LLM-Judge → Entscheidung, mit Audit-Hook.

Entscheidungslogik:

1. Die Regelschicht berechnet einen Risikowert. ``score >= block_threshold`` → BLOCK,
   ``score >= review_threshold`` → REVIEW, sonst ALLOW.
2. Ist ein Judge konfiguriert, wird er im Modus ``uncertain`` (Standard) nur bei REVIEW gefragt,
   im Modus ``always`` bei REVIEW und ALLOW. Eine BLOCK-Entscheidung der Regeln kann der Judge
   nie aufheben.
3. Judge-Urteil ``injection`` mit ausreichender Konfidenz → BLOCK; ``benign`` mit ausreichender
   Konfidenz → ALLOW (nur wenn ``judge_can_allow``); sonst ``judge_uncertain_decision``.
4. Jeder Judge-Fehler (Zeitüberschreitung, Netzfehler, ungültige Antwort, Ausnahme in einem
   eigenen Judge) führt zu ``judge_failure_decision`` (Standard BLOCK; REVIEW möglich; ALLOW
   ist nicht erlaubt, die Pipeline ist fail-closed).
5. Der Audit-Hook erhält je Entscheidung ein :class:`AuditEvent`. Standardmässig ohne
   Klartext, nur mit SHA-256-Hash und Länge der Eingabe (Datensparsamkeit).
"""

from __future__ import annotations

import enum
import hashlib
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .engine import EngineConfig, analyze, risk_score
from .judge import Judge, JudgeVerdict
from .models import Context, Decision, Finding, JudgeOutcome, ScanResult
from .tool_policy import Tool, ToolPolicy, analyze_tool_input

__all__ = [
    "AuditEvent",
    "Guard",
    "GuardConfig",
    "JudgeMode",
    "scan",
    "scan_document",
    "scan_tool_input",
]

logger = logging.getLogger(__name__)


class JudgeMode(str, enum.Enum):
    """Wann der Judge gefragt wird."""

    NEVER = "never"
    UNCERTAIN = "uncertain"
    ALWAYS = "always"


@dataclass(frozen=True, slots=True)
class GuardConfig:
    """Konfiguration der Pipeline. Alle Felder haben vorsichtige Standardwerte."""

    review_threshold: float = 0.4
    block_threshold: float = 0.7
    engine: EngineConfig = field(default_factory=EngineConfig)
    tool_policy: ToolPolicy = field(default_factory=ToolPolicy)
    judge_mode: JudgeMode = JudgeMode.UNCERTAIN
    judge_failure_decision: Decision = Decision.BLOCK
    judge_uncertain_decision: Decision = Decision.REVIEW
    judge_min_confidence: float = 0.7
    judge_can_allow: bool = True
    truncation_decision: Decision = Decision.REVIEW
    strict_audit: bool = False
    audit_include_text: bool = False

    def __post_init__(self) -> None:
        if not 0.0 < self.review_threshold <= self.block_threshold <= 1.0:
            raise ValueError("Es muss 0 < review_threshold <= block_threshold <= 1 gelten")
        if self.judge_failure_decision is Decision.ALLOW:
            raise ValueError("judge_failure_decision=ALLOW wäre fail-open und ist nicht erlaubt")
        if self.judge_uncertain_decision is Decision.ALLOW:
            raise ValueError("judge_uncertain_decision=ALLOW ist nicht erlaubt")
        if not 0.0 <= self.judge_min_confidence <= 1.0:
            raise ValueError("judge_min_confidence muss in [0, 1] liegen")


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Protokolleintrag je Entscheidung. ``text`` nur bei ``audit_include_text=True``."""

    timestamp: str
    context: str
    decision: str
    rule_decision: str
    score: float
    rule_ids: tuple[str, ...]
    input_sha256: str
    input_chars: int
    truncated: bool
    judge_verdict: str | None = None
    judge_confidence: float | None = None
    judge_error: str | None = None
    judge_attempts: int = 0
    source: str | None = None
    tool: str | None = None
    text: str | None = None
    reasons: tuple[str, ...] = ()


AuditHook = Callable[[AuditEvent], None]


class Guard:
    """Zentrale Klasse. Ohne Judge arbeitet sie rein regelbasiert, deterministisch und offline."""

    def __init__(
        self,
        config: GuardConfig | None = None,
        *,
        judge: Judge | None = None,
        audit: AuditHook | None = None,
    ) -> None:
        self.config = config or GuardConfig()
        self.judge = judge
        self.audit = audit

    # ------------------------------------------------------------------ öffentliche API
    def scan(self, text: str) -> ScanResult:
        """Prüft eine direkte Eingabe (Chat-Nachricht) auf Prompt-Injection."""
        return self._scan_text(text, Context.CHAT, source=None)

    def scan_document(self, text: str, *, source: str | None = None) -> ScanResult:
        """Prüft nicht vertrauenswürdigen Inhalt (RAG-Chunk, E-Mail, Webseite) auf indirekte Injection."""
        return self._scan_text(text, Context.DOCUMENT, source=source)

    def scan_tool_input(self, value: str, tool: Tool | str = Tool.SHELL) -> ScanResult:
        """Prüft eine Zeichenkette, die ein Werkzeug gleich ausführen wird (nur Regeln, kein Judge)."""
        selected = Tool(tool)
        findings = analyze_tool_input(value, selected, self.config.tool_policy)
        score = risk_score(findings)
        decision = self._threshold(score)
        reasons = (self._rule_reason(score, decision),)
        result = ScanResult(decision, score, Context.TOOL_INPUT, tuple(findings), decision, None, False, reasons)
        return self._emit(result, value, source=None, tool=selected.value)

    # ------------------------------------------------------------------ intern
    def _threshold(self, score: float) -> Decision:
        if score >= self.config.block_threshold:
            return Decision.BLOCK
        if score >= self.config.review_threshold:
            return Decision.REVIEW
        return Decision.ALLOW

    def _rule_reason(self, score: float, decision: Decision) -> str:
        return (
            f"Regelschicht: Risikowert {score:.2f} → {decision.value} "
            f"(review ab {self.config.review_threshold:.2f}, block ab {self.config.block_threshold:.2f})"
        )

    def _scan_text(self, text: str, context: Context, *, source: str | None) -> ScanResult:
        findings, truncated = analyze(text, context, self.config.engine)
        score = risk_score(findings)
        rule_decision = self._threshold(score)
        reasons = [self._rule_reason(score, rule_decision)]
        if truncated:
            rule_decision = Decision.strictest(rule_decision, self.config.truncation_decision)
            reasons.append(f"Eingabe gekürzt auf {self.config.engine.max_input_chars} Zeichen")
        decision = rule_decision
        outcome: JudgeOutcome | None = None
        if self._should_ask_judge(rule_decision):
            outcome, decision, judge_reason = self._ask_judge(text, context, findings, rule_decision)
            reasons.append(judge_reason)
        result = ScanResult(
            decision,
            score,
            context,
            tuple(findings),
            rule_decision,
            outcome,
            truncated,
            tuple(reasons),
        )
        return self._emit(result, text, source=source, tool=None)

    def _should_ask_judge(self, rule_decision: Decision) -> bool:
        if self.judge is None or self.config.judge_mode is JudgeMode.NEVER:
            return False
        if rule_decision is Decision.BLOCK:
            return False
        return self.config.judge_mode is JudgeMode.ALWAYS or rule_decision is Decision.REVIEW

    def _ask_judge(
        self,
        text: str,
        context: Context,
        findings: list[Finding],
        rule_decision: Decision,
    ) -> tuple[JudgeOutcome, Decision, str]:
        assert self.judge is not None  # noqa: S101 - durch _should_ask_judge garantiert
        hints = tuple(dict.fromkeys(f"{f.rule_id}:{f.severity.value}" for f in findings))
        started = time.perf_counter()
        try:
            verdict: JudgeVerdict = self.judge.evaluate(text, context=context, hints=hints)
        except Exception as exc:  # noqa: BLE001 - jeder Fehler eines Judges führt bewusst zu fail-closed
            latency = (time.perf_counter() - started) * 1000
            attempts = getattr(exc, "attempts", 0)
            message = f"{type(exc).__name__}: {exc}"[:300]
            outcome = JudgeOutcome(None, None, None, None, message, attempts, latency)
            decision = Decision.strictest(rule_decision, self.config.judge_failure_decision)
            logger.warning("Judge-Fehler, fail-closed (%s): %s", decision.value, message)
            return outcome, decision, f"Judge-Fehler ({message}) → fail-closed: {decision.value}"
        latency = (time.perf_counter() - started) * 1000
        outcome = JudgeOutcome(verdict.verdict, verdict.category, verdict.confidence, verdict.reason, None, 1, latency)
        confident = verdict.confidence >= self.config.judge_min_confidence
        if verdict.verdict == "injection" and confident:
            decision = Decision.BLOCK
        elif verdict.verdict == "benign" and confident and self.config.judge_can_allow:
            decision = Decision.ALLOW
        else:
            decision = Decision.strictest(rule_decision, self.config.judge_uncertain_decision)
        reason = f"Judge: {verdict.verdict} ({verdict.confidence:.2f}) → {decision.value}"
        return outcome, decision, reason

    def _emit(self, result: ScanResult, text: str, *, source: str | None, tool: str | None) -> ScanResult:
        if self.audit is None:
            return result
        judge = result.judge
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            context=result.context.value,
            decision=result.decision.value,
            rule_decision=result.rule_decision.value,
            score=round(result.score, 4),
            rule_ids=result.rule_ids,
            input_sha256=hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest(),
            input_chars=len(text),
            truncated=result.truncated,
            judge_verdict=judge.verdict if judge else None,
            judge_confidence=judge.confidence if judge else None,
            judge_error=judge.error if judge else None,
            judge_attempts=judge.attempts if judge else 0,
            source=source,
            tool=tool,
            text=text if self.config.audit_include_text else None,
            reasons=result.reasons,
        )
        try:
            self.audit(event)
        except Exception:
            logger.exception("Audit-Hook ist fehlgeschlagen")
            if self.config.strict_audit:
                return ScanResult(
                    Decision.BLOCK,
                    result.score,
                    result.context,
                    result.findings,
                    result.rule_decision,
                    result.judge,
                    result.truncated,
                    (*result.reasons, "Audit fehlgeschlagen und strict_audit aktiv → block"),
                )
        return result


_DEFAULT = Guard()


def scan(text: str) -> ScanResult:
    """Prüft eine Chat-Eingabe mit der Standardkonfiguration (nur Regeln, offline)."""
    return _DEFAULT.scan(text)


def scan_document(text: str, *, source: str | None = None) -> ScanResult:
    """Prüft ein Dokument (RAG-Chunk, E-Mail, Webseite) mit der Standardkonfiguration."""
    return _DEFAULT.scan_document(text, source=source)


def scan_tool_input(value: str, tool: Tool | str = Tool.SHELL, *, policy: ToolPolicy | None = None) -> ScanResult:
    """Prüft eine Tool-Eingabe (``shell``, ``sql``, ``url``, ``path``)."""
    if policy is None:
        return _DEFAULT.scan_tool_input(value, tool)
    return Guard(GuardConfig(tool_policy=policy)).scan_tool_input(value, tool)
