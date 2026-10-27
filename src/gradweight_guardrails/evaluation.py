"""Benchmark: Datensätze laden, Guard ausführen, Metriken berechnen, Bericht und Gate.

Zählweise (ehrlich, ohne Umetikettierung):

* Positiv ist jeder Fall mit ``label = "attack"``. Jede Umgehung ist ein False Negative.
* Hauptmetrik «markiert»: Entscheidung REVIEW oder BLOCK gilt als Erkennung. Zusätzlich wird
  «blockiert» (nur BLOCK) berichtet.
* Precision, Recall, F1 und False-Positive-Rate werden je Split (dev/holdout), Sprache und
  Kategorie getrennt ausgewiesen. Undefinierte Werte (Division durch null) erscheinen als «–».
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .guard import Guard
from .models import Decision, ScanResult

__all__ = [
    "Case",
    "CaseResult",
    "GateResult",
    "Metrics",
    "check_baseline",
    "evaluate",
    "load_cases",
    "make_baseline",
    "metrics_for",
    "readme_block",
    "render_report",
]

_REQUIRED = ("id", "split", "lang", "category", "context", "label", "technique", "text", "note")
_CONTEXTS = ("chat", "document", "tool")
_LABELS = ("attack", "benign")
GATE_METRICS = ("precision", "recall", "f1", "fpr")


@dataclass(frozen=True, slots=True)
class Case:
    id: str
    split: str
    lang: str
    category: str
    context: str
    label: str
    technique: str
    text: str
    note: str
    tool: str | None = None

    @property
    def is_attack(self) -> bool:
        return self.label == "attack"


@dataclass(frozen=True, slots=True)
class CaseResult:
    case: Case
    decision: Decision
    rule_ids: tuple[str, ...]
    score: float

    @property
    def flagged(self) -> bool:
        return self.decision is not Decision.ALLOW

    @property
    def blocked(self) -> bool:
        return self.decision is Decision.BLOCK


@dataclass(frozen=True, slots=True)
class Metrics:
    tp: int
    fp: int
    tn: int
    fn: int

    @property
    def n(self) -> int:
        return self.tp + self.fp + self.tn + self.fn

    @property
    def precision(self) -> float | None:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else None

    @property
    def recall(self) -> float | None:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else None

    @property
    def fpr(self) -> float | None:
        return self.fp / (self.fp + self.tn) if self.fp + self.tn else None

    @property
    def f1(self) -> float | None:
        p, r = self.precision, self.recall
        if p is None or r is None or p + r == 0:
            return None
        return 2 * p * r / (p + r)

    def as_dict(self) -> dict[str, Any]:
        return {
            "tp": self.tp,
            "fp": self.fp,
            "tn": self.tn,
            "fn": self.fn,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "fpr": self.fpr,
        }


@dataclass(frozen=True, slots=True)
class GateResult:
    ok: bool
    failures: tuple[str, ...] = field(default=())


def load_cases(path: Path | str) -> list[Case]:
    """Lädt eine JSONL-Datei und prüft das Schema jedes Falls."""
    cases: list[Case] = []
    seen: set[str] = set()
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            raw = json.loads(line)
            missing = [key for key in _REQUIRED if key not in raw]
            if missing:
                raise ValueError(f"{path}:{line_number}: Felder fehlen: {missing}")
            if raw["context"] not in _CONTEXTS or raw["label"] not in _LABELS:
                raise ValueError(f"{path}:{line_number}: context/label ungültig")
            if raw["context"] == "tool" and not raw.get("tool"):
                raise ValueError(f"{path}:{line_number}: Tool-Fall ohne 'tool'")
            if raw["id"] in seen:
                raise ValueError(f"{path}:{line_number}: doppelte ID {raw['id']}")
            seen.add(raw["id"])
            cases.append(Case(**{key: raw[key] for key in _REQUIRED}, tool=raw.get("tool")))
    return cases


def _run(guard: Guard, case: Case) -> ScanResult:
    if case.context == "chat":
        return guard.scan(case.text)
    if case.context == "document":
        return guard.scan_document(case.text)
    return guard.scan_tool_input(case.text, case.tool or "shell")


def evaluate(cases: Iterable[Case], guard: Guard | None = None) -> list[CaseResult]:
    """Führt alle Fälle durch den Guard (Standard: nur Regeln, offline, deterministisch)."""
    guard = guard or Guard()
    results: list[CaseResult] = []
    for case in cases:
        result = _run(guard, case)
        results.append(CaseResult(case, result.decision, result.rule_ids, result.score))
    return results


def metrics_for(results: Iterable[CaseResult], *, blocked_only: bool = False) -> Metrics:
    tp = fp = tn = fn = 0
    for result in results:
        positive = result.blocked if blocked_only else result.flagged
        if result.case.is_attack:
            tp += positive
            fn += not positive
        else:
            fp += positive
            tn += not positive
    return Metrics(tp, fp, tn, fn)


def _group(results: Sequence[CaseResult], key: Callable[[CaseResult], str]) -> dict[str, list[CaseResult]]:
    groups: dict[str, list[CaseResult]] = {}
    for result in results:
        groups.setdefault(key(result), []).append(result)
    return dict(sorted(groups.items()))


def _pct(value: float | None) -> str:
    return "–" if value is None else f"{value * 100:.1f} %"


def _escape(text: str, limit: int = 90) -> str:
    out = []
    for c in text:
        if c == "\n":
            out.append("⏎")
        elif not c.isprintable() or c in "­":
            out.append(f"\\u{ord(c):04x}" if ord(c) <= 0xFFFF else f"\\U{ord(c):08x}")
        else:
            out.append(c)
    escaped = "".join(out)
    if len(escaped) > limit:
        escaped = escaped[: limit - 1] + "…"
    return escaped.replace("|", "\\|").replace("`", "'")


def sha256_file(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _metrics_row(label: str, results: Sequence[CaseResult]) -> str:
    m = metrics_for(results)
    b = metrics_for(results, blocked_only=True)
    attacks = sum(r.case.is_attack for r in results)
    return (
        f"| {label} | {len(results)} | {attacks} | {len(results) - attacks} | {_pct(m.precision)} | "
        f"{_pct(m.recall)} | {_pct(m.f1)} | {_pct(m.fpr)} | {_pct(b.recall)} | {_pct(b.fpr)} |"
    )


_TABLE_HEADER = (
    "| Gruppe | Fälle | Angriffe | Harmlos | Precision | Recall | F1 | FPR | Recall (nur BLOCK) | FPR (nur BLOCK) |\n"
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
)


def _split_section(name: str, results: Sequence[CaseResult]) -> list[str]:
    lines = [f"## Split «{name}»", "", "### Nach Sprache", "", _TABLE_HEADER]
    for lang, group in _group(results, lambda r: r.case.lang).items():
        lines.append(_metrics_row(lang, group))
    lines += ["", "### Nach Kategorie", "", _TABLE_HEADER]
    for category, group in _group(results, lambda r: r.case.category).items():
        lines.append(_metrics_row(category, group))
    obfuscated = [r for r in results if r.case.category == "obfuscated"]
    if obfuscated:
        lines += [
            "",
            "### Obfuskierte Angriffe nach Technik",
            "",
            "| Technik | Fälle | erkannt | verpasst |",
            "|---|---:|---:|---:|",
        ]
        for technique, group in _group(obfuscated, lambda r: r.case.technique).items():
            hit = sum(r.flagged for r in group)
            lines.append(f"| {technique} | {len(group)} | {hit} | {len(group) - hit} |")
    misses = [r for r in results if r.case.is_attack and not r.flagged]
    false_alarms = [r for r in results if not r.case.is_attack and r.flagged]
    lines += ["", f"### Verpasste Angriffe (False Negatives): {len(misses)}", ""]
    if misses:
        lines += ["| ID | Sprache | Kategorie | Technik | Text |", "|---|---|---|---|---|"]
        for r in misses:
            c = r.case
            lines.append(f"| {c.id} | {c.lang} | {c.category} | {c.technique} | `{_escape(c.text)}` |")
    lines += ["", f"### Fehlalarme (False Positives): {len(false_alarms)}", ""]
    if false_alarms:
        lines += [
            "| ID | Sprache | Kategorie | Entscheidung | Regeln | Text |",
            "|---|---|---|---|---|---|",
        ]
        for r in false_alarms:
            c = r.case
            rules = ", ".join(r.rule_ids)
            lines.append(f"| {c.id} | {c.lang} | {c.category} | {r.decision.value} | {rules} | `{_escape(c.text)}` |")
    lines.append("")
    return lines


def render_report(
    results_by_split: dict[str, list[CaseResult]],
    *,
    dataset_hashes: dict[str, str],
    version: str,
) -> str:
    """Erzeugt ``bench/ERGEBNISSE.md``. Der Inhalt ist deterministisch (kein Datum)."""
    lines = [
        "# Benchmark-Ergebnisse",
        "",
        "Diese Datei wird von `scripts/generate_reports.py` erzeugt. Nicht von Hand bearbeiten;",
        "`tests/test_doku_konsistenz.py` prüft, dass sie zum aktuellen Code passt.",
        "",
        f"- Paketversion: `{version}`",
        "- Konfiguration: Standard-`Guard()` ohne LLM-Judge (nur Regelschicht, offline, deterministisch)",
    ]
    for name, digest in dataset_hashes.items():
        lines.append(f"- `{name}`: SHA-256 `{digest}`")
    lines += [
        "",
        "Zählweise: Ein Angriff gilt als erkannt, wenn die Entscheidung REVIEW oder BLOCK lautet",
        "(Spalten Precision bis FPR). Die beiden letzten Spalten zählen nur BLOCK. Jede Umgehung",
        "zählt als False Negative. Methodik und Einschränkungen: `bench/README.md`.",
        "",
        "## Übersicht",
        "",
        _TABLE_HEADER,
    ]
    for name, results in results_by_split.items():
        lines.append(_metrics_row(name, results))
    lines.append("")
    for name, results in results_by_split.items():
        lines += _split_section(name, results)
    return "\n".join(lines).rstrip() + "\n"


def readme_block(results_by_split: dict[str, list[CaseResult]]) -> str:
    """Kurztabelle für die README (zwischen den BENCH-Markern)."""
    lines = [
        "| Split | Fälle | Precision | Recall | F1 | FPR | Recall (nur BLOCK) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, results in results_by_split.items():
        m = metrics_for(results)
        b = metrics_for(results, blocked_only=True)
        lines.append(
            f"| {name} | {len(results)} | {_pct(m.precision)} | {_pct(m.recall)} | {_pct(m.f1)} | "
            f"{_pct(m.fpr)} | {_pct(b.recall)} |"
        )
    holdout = results_by_split.get("holdout")
    if holdout:
        lines += [
            "",
            "Holdout nach Sprache:",
            "",
            "| Sprache | Fälle | Recall | FPR |",
            "|---|---:|---:|---:|",
        ]
        for lang, group in _group(holdout, lambda r: r.case.lang).items():
            m = metrics_for(group)
            lines.append(f"| {lang} | {len(group)} | {_pct(m.recall)} | {_pct(m.fpr)} |")
    return "\n".join(lines)


def make_baseline(results_by_split: dict[str, list[CaseResult]], *, tolerance: float = 0.02) -> dict[str, Any]:
    """Erzeugt den Inhalt von ``bench/baseline.json`` aus aktuellen Ergebnissen."""
    splits: dict[str, Any] = {}
    for name, results in results_by_split.items():
        metrics = metrics_for(results).as_dict()
        splits[name] = {key: metrics[key] for key in GATE_METRICS}
    return {"tolerance": tolerance, "splits": splits}


def check_baseline(results_by_split: dict[str, list[CaseResult]], baseline: dict[str, Any]) -> GateResult:
    """Vergleicht aktuelle Metriken mit der Baseline.

    Fehlschlag, wenn Precision, Recall oder F1 um mehr als ``tolerance`` sinken oder die FPR um
    mehr als ``tolerance`` steigt. Fehlt ein Split oder eine Metrik in der Baseline, ist das
    ebenfalls ein Fehlschlag (die Baseline wird gelesen, nicht übersprungen).
    """
    tolerance = float(baseline["tolerance"])
    failures: list[str] = []
    for name, results in results_by_split.items():
        reference = baseline.get("splits", {}).get(name)
        if reference is None:
            failures.append(f"{name}: kein Eintrag in der Baseline")
            continue
        current = metrics_for(results).as_dict()
        for key in GATE_METRICS:
            if key not in reference:
                failures.append(f"{name}.{key}: fehlt in der Baseline")
                continue
            base_value, value = reference[key], current[key]
            if base_value is None or value is None:
                if base_value != value:
                    failures.append(f"{name}.{key}: {value} statt {base_value}")
                continue
            if key == "fpr" and value > base_value + tolerance:
                failures.append(f"{name}.fpr: {value:.4f} > {base_value:.4f} + {tolerance}")
            if key != "fpr" and value < base_value - tolerance:
                failures.append(f"{name}.{key}: {value:.4f} < {base_value:.4f} − {tolerance}")
    return GateResult(not failures, tuple(failures))
