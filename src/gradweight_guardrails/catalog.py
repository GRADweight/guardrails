"""Regelkatalog als Daten und als Markdown (Quelle für ``docs/regeln.md`` und ``rules``-Befehl)."""

from __future__ import annotations

from typing import Any

from .models import Context
from .output import OUTPUT_RULES
from .rules import META_RULES, RULES
from .tool_policy import TOOL_RULES

__all__ = ["catalog", "render_catalog"]


def catalog() -> list[dict[str, Any]]:
    """Alle Regeln mit ID, Bereich, Kategorie, Schweregrad und Beschreibung."""
    entries: list[dict[str, Any]] = []
    for rule in RULES:
        contexts = sorted(c.value for c in rule.contexts)
        severity = rule.severity.value
        if rule.document_severity is not None and rule.document_severity is not rule.severity:
            severity = f"{rule.severity.value} (Dokument: {rule.document_severity.value})"
        entries.append(
            {
                "id": rule.id,
                "scope": "/".join(contexts),
                "category": rule.category.value,
                "severity": severity,
                "description": rule.description,
                "examples": list(rule.examples),
            }
        )
    for meta in META_RULES:
        entries.append(
            {
                "id": meta.id,
                "scope": f"{Context.CHAT.value}/{Context.DOCUMENT.value}",
                "category": meta.category.value,
                "severity": meta.severity.value,
                "description": meta.description,
                "examples": [],
            }
        )
    for tool_rule in TOOL_RULES:
        entries.append(
            {
                "id": tool_rule.id,
                "scope": f"tool:{tool_rule.tool.value}",
                "category": tool_rule.category.value,
                "severity": tool_rule.severity.value,
                "description": tool_rule.description,
                "examples": [],
            }
        )
    for rule_id, category, severity_value, description in OUTPUT_RULES:
        entries.append(
            {
                "id": rule_id,
                "scope": Context.OUTPUT.value,
                "category": category.value,
                "severity": severity_value.value,
                "description": description,
                "examples": [],
            }
        )
    return entries


def render_catalog() -> str:
    """Markdown für ``docs/regeln.md``."""
    lines = [
        "# Regelkatalog",
        "",
        "Diese Datei wird von `scripts/generate_reports.py` aus dem Code erzeugt und von",
        "`tests/test_doku_konsistenz.py` geprüft. Die IDs sind stabil: Eine Regel behält ihre ID,",
        "auch wenn sich ihr Muster ändert. Entfernte IDs werden nicht neu vergeben.",
        "",
        "Schweregrade und Gewichte im Risikowert: low 0.2, medium 0.5, high 0.75, critical 0.95.",
        "Der Risikowert ist 1 − Π(1 − Gewicht) über den höchsten Schweregrad je Regel-ID.",
        "",
        "| ID | Bereich | Kategorie | Schweregrad | Beschreibung | Beispiele |",
        "|---|---|---|---|---|---|",
    ]
    for entry in catalog():
        examples = "; ".join(_code(e) for e in entry["examples"]) or "–"
        lines.append(
            f"| {entry['id']} | {entry['scope']} | {entry['category']} | {entry['severity']} | "
            f"{_cell(entry['description'])} | {examples} |"
        )
    return "\n".join(lines) + "\n"


def _cell(text: str) -> str:
    """Tabellenzelle: Pipe maskieren, spitze Klammern als Entitäten (sonst als HTML gedeutet)."""
    return text.replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;")


def _code(text: str) -> str:
    """Beispiel als Code-Span; in GitHub-Tabellen muss die Pipe auch dort maskiert werden."""
    return "`" + text.replace("`", "'").replace("|", "\\|") + "`"
