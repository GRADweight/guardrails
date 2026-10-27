"""Datenmodell: Entscheidungen, Schweregrade, Kategorien, Befunde und Ergebnisse."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "Category",
    "Context",
    "Decision",
    "Finding",
    "JudgeOutcome",
    "ScanResult",
    "Severity",
]


class Decision(str, enum.Enum):
    """Ergebnis einer Prüfung. Die Reihenfolge ALLOW < REVIEW < BLOCK ist die Strenge."""

    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"

    @property
    def rank(self) -> int:
        return _DECISION_RANK[self]

    @classmethod
    def strictest(cls, *decisions: Decision) -> Decision:
        """Gibt die strengste der übergebenen Entscheidungen zurück (ALLOW, wenn leer)."""
        result = cls.ALLOW
        for decision in decisions:
            if decision.rank > result.rank:
                result = decision
        return result


_DECISION_RANK = {Decision.ALLOW: 0, Decision.REVIEW: 1, Decision.BLOCK: 2}


class Severity(str, enum.Enum):
    """Schweregrad eines Befunds. Das Gewicht fliesst in den Risikowert ein."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def weight(self) -> float:
        return _SEVERITY_WEIGHT[self]

    @property
    def level(self) -> int:
        return _SEVERITY_ORDER.index(self)

    def shifted(self, steps: int) -> Severity:
        """Verschiebt den Schweregrad um ``steps`` Stufen (begrenzt auf LOW..CRITICAL)."""
        index = max(0, min(len(_SEVERITY_ORDER) - 1, self.level + steps))
        return _SEVERITY_ORDER[index]

    @classmethod
    def max(cls, a: Severity, b: Severity) -> Severity:
        return a if a.level >= b.level else b


_SEVERITY_ORDER = (Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL)
_SEVERITY_WEIGHT = {
    Severity.LOW: 0.2,
    Severity.MEDIUM: 0.5,
    Severity.HIGH: 0.75,
    Severity.CRITICAL: 0.95,
}


class Category(str, enum.Enum):
    """Regelfamilie eines Befunds."""

    INSTRUCTION_OVERRIDE = "instruction_override"
    ROLE_HIJACK = "role_hijack"
    PROMPT_LEAK = "prompt_leak"
    DELIMITER_INJECTION = "delimiter_injection"
    DATA_EXFILTRATION = "data_exfiltration"
    TOOL_ABUSE = "tool_abuse"
    INDIRECT_INSTRUCTION = "indirect_instruction"
    OBFUSCATION = "obfuscation"
    RESOURCE_LIMIT = "resource_limit"
    TOOL_SHELL = "tool_shell"
    TOOL_SQL = "tool_sql"
    TOOL_NETWORK = "tool_network"
    TOOL_PATH = "tool_path"
    CANARY_LEAK = "canary_leak"
    SYSTEM_PROMPT_LEAK = "system_prompt_leak"
    PII = "pii"
    OUTPUT_EXFILTRATION = "output_exfiltration"
    JUDGE = "judge"


class Context(str, enum.Enum):
    """Einsatzkontext einer Prüfung."""

    CHAT = "chat"
    """Direkte Eingabe eines Menschen an das Modell."""
    DOCUMENT = "document"
    """Nicht vertrauenswürdiger Inhalt, der ins Modell gelangt (RAG-Chunk, E-Mail, Webseite)."""
    TOOL_INPUT = "tool_input"
    """Zeichenkette, die ein Tool gleich ausführen wird (Shell, SQL, URL, Pfad)."""
    OUTPUT = "output"
    """Antwort des Modells, bevor sie den Nutzer oder ein Folgesystem erreicht."""


@dataclass(frozen=True, slots=True)
class Finding:
    """Ein einzelner Befund einer Regel.

    ``span`` bezieht sich immer auf den Originaltext (Zeichenindizes, Ende exklusiv).
    ``layer`` beschreibt, in welcher Sicht der Treffer entstand, z.B. ``words`` (normalisiert),
    ``leet``, ``compact`` (Sperrschrift aufgehoben), ``rot13`` oder ``base64>words``.
    """

    rule_id: str
    category: Category
    severity: Severity
    language: str
    span: tuple[int, int]
    excerpt: str
    description: str
    layer: str = "words"
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "language": self.language,
            "span": list(self.span),
            "excerpt": self.excerpt,
            "description": self.description,
            "layer": self.layer,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class JudgeOutcome:
    """Was der LLM-Judge geliefert hat, oder warum er nicht verwendbar war."""

    verdict: str | None
    category: str | None
    confidence: float | None
    reason: str | None
    error: str | None = None
    attempts: int = 0
    latency_ms: float = 0.0

    @property
    def ok(self) -> bool:
        return self.error is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "category": self.category,
            "confidence": self.confidence,
            "reason": self.reason,
            "error": self.error,
            "attempts": self.attempts,
            "latency_ms": round(self.latency_ms, 3),
        }


@dataclass(frozen=True, slots=True)
class ScanResult:
    """Ergebnis einer Prüfung.

    ``rule_decision`` ist die Entscheidung der Regelschicht allein; ``decision`` ist die
    endgültige Entscheidung nach einem allfälligen LLM-Judge.
    """

    decision: Decision
    score: float
    context: Context
    findings: tuple[Finding, ...]
    rule_decision: Decision
    judge: JudgeOutcome | None = None
    truncated: bool = False
    reasons: tuple[str, ...] = field(default=())

    @property
    def blocked(self) -> bool:
        return self.decision is Decision.BLOCK

    @property
    def allowed(self) -> bool:
        return self.decision is Decision.ALLOW

    @property
    def rule_ids(self) -> tuple[str, ...]:
        seen: dict[str, None] = {}
        for finding in self.findings:
            seen.setdefault(finding.rule_id, None)
        return tuple(seen)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "score": round(self.score, 4),
            "context": self.context.value,
            "rule_decision": self.rule_decision.value,
            "truncated": self.truncated,
            "reasons": list(self.reasons),
            "findings": [f.to_dict() for f in self.findings],
            "judge": self.judge.to_dict() if self.judge else None,
        }
