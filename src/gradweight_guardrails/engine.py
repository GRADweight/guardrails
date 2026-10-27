"""Regelschicht: wendet den Regelkatalog auf alle Sichten an und bewertet die Befunde.

Ablauf je Text:

1. Normalisieren (mehrere Sichten, siehe :mod:`normalize`).
2. Jede Regel auf ihre Sichten anwenden, Validatoren prüfen, Treffer auf den Originaltext
   zurückführen.
3. Treffer, die nur in einer entschleierten Sicht auftreten (Leetspeak, Sperrschrift, ROT13,
   rückwärts), werden markiert und mindestens als HIGH gewertet.
4. Kontextregeln anwenden: im Chat wird eine Erwähnung in Anführungszeichen innerhalb einer
   Frage über Angriffe abgeschwächt, ebenso Fragen in der ersten Person («Wie sende ich …?»).
5. Kodierte Segmente (Base64, Hex, URL, HTML, Unicode) dekodieren und rekursiv prüfen,
   begrenzt durch Tiefe und Budget.
6. Risikowert: 1 − Π(1 − Gewicht) über den höchsten Schweregrad je Regel-ID.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .decode import DecodeBudget, find_encoded_segments
from .lexicon import attribute_language
from .models import Category, Context, Finding, Severity
from .normalize import Normalized, Signal, normalize
from .rules import META_RULES, MatchContext, Rule, compiled_pattern, prefilter_passes, rules_for

__all__ = ["EngineConfig", "analyze", "risk_score", "warmup"]

PRIMARY_VIEWS = frozenset({"words", "text"})
MAX_FINDINGS_PER_RULE = 25
"""Obergrenze je Regel und Text; der Risikowert hängt ohnehin nur vom stärksten Treffer ab."""
_META_BY_ID = {meta.id: meta for meta in META_RULES}
_EXCERPT_CHARS = 160

_META_CUES = re.compile(
    r"\b(?:what (?:is|are|does|do|s)|what s|how (?:do|can|should|would) (?:i|we)|explain\w*|examples?|meaning|"
    r"means?|is (?:this|that|it) (?:a|an|real)|attacks?|attackers?|injections?|jailbreaks?|pentest\w*|"
    r"security|training|blog|article|paper|detect\w*|defend\w*|mitigat\w*|"
    r"was (?:ist|sind|bedeutet|heisst)|wie (?:erkenne|kann|soll|verhindere|schutze)|erklar\w*|beispiel\w*|"
    r"bedeutet|bedeutung|angriff\w*|angreifer\w*|sicherheit\w*|schulung|artikel|erkenn\w*|abwehr\w*|"
    r"qu est ce|signifie|explique\w*|exemples?|attaques?|securite|formation|detecter|"
    r"cos e|che cos e|significa|spiega\w*|esemp[io]|attacc\w*|sicurezza|formazione|articolo|rilevare|"
    r"heisst)\b"
)
_INTERROGATIVE = re.compile(
    r"^(?:how|what|why|where|when|which|who|can i|could i|should i|do i|is it|is there|"
    r"wie|was|warum|wieso|weshalb|wo|wann|welche\w*|kann ich|soll ich|muss ich|darf ich|gibt es|"
    r"comment|que|quoi|pourquoi|ou|quand|quel\w*|puis je|est ce que|peut on|dois je|"
    r"come|cosa|che|perche|dove|quando|qual\w*|posso|devo|si puo)\b"
)
_FIRST_PERSON_Q = re.compile(
    r"\b(?:i|we|my|our|ich|wir|mein\w*|unser\w*|je|j|nous|mon|ma|mes|notre|nos|io|noi|mio|mia|miei|mie|"
    r"nostr[oaie]|posso|possiamo|devo|dobbiamo)\b"
)
_SENTENCE_END = re.compile(r"[.!?\n]")
_OPENERS = "\"«„“‘'`‹"
_CLOSERS = "\"»“”’'`›"


@dataclass(frozen=True, slots=True)
class EngineConfig:
    """Parameter der Regelschicht."""

    max_input_chars: int = 50_000
    decode_depth: int = 2
    max_decoded_segments: int = 16
    max_decoded_chars: int = 65_536
    mention_dampening: bool = True
    question_dampening: bool = True

    def __post_init__(self) -> None:
        if self.max_input_chars < 1:
            raise ValueError("max_input_chars muss positiv sein")
        if self.decode_depth < 0:
            raise ValueError("decode_depth darf nicht negativ sein")


def risk_score(findings: tuple[Finding, ...] | list[Finding]) -> float:
    """Kombinierter Risikowert in [0, 1] (Noisy-OR über den höchsten Schweregrad je Regel)."""
    best: dict[str, Severity] = {}
    for finding in findings:
        current = best.get(finding.rule_id)
        best[finding.rule_id] = finding.severity if current is None else Severity.max(current, finding.severity)
    remaining = 1.0
    for severity in best.values():
        remaining *= 1.0 - severity.weight
    return 1.0 - remaining


def warmup() -> None:
    """Kompiliert alle Muster im Voraus (sonst geschieht das beim ersten Aufruf)."""
    for context in (Context.CHAT, Context.DOCUMENT):
        for rule in rules_for(context):
            for view in rule.views:
                compiled_pattern(rule, view)


def _excerpt(text: str, span: tuple[int, int]) -> str:
    snippet = text[span[0] : span[1]]
    if len(snippet) > _EXCERPT_CHARS:
        snippet = snippet[: _EXCERPT_CHARS - 1] + "…"
    return snippet


def _sentence(text: str, span: tuple[int, int], limit: int = 400) -> str:
    """Satz um ``span`` (begrenzt auf ``limit`` Zeichen je Richtung, damit die Laufzeit linear bleibt)."""
    floor = max(0, span[0] - limit)
    start = span[0]
    while start > floor and not _SENTENCE_END.match(text[start - 1]):
        start -= 1
    ceiling = min(len(text), span[1] + limit)
    end = span[1]
    while end < ceiling and not _SENTENCE_END.match(text[end]):
        end += 1
    if end < len(text):
        end += 1
    return text[start:end]


def _inside_quotes(text: str, span: tuple[int, int]) -> bool:
    left = text[max(0, span[0] - 200) : span[0]]
    right = text[span[1] : span[1] + 200]
    opener = -1
    for i in range(len(left) - 1, -1, -1):
        c = left[i]
        if c == "\n":
            return False
        if c in _OPENERS:
            if c in "'‘" and i > 0 and left[i - 1].isalpha():
                continue
            opener = i
            break
    if opener < 0:
        return False
    for j, c in enumerate(right):
        if c == "\n":
            return False
        if c in _CLOSERS:
            if c in "'’" and j + 1 < len(right) and right[j + 1].isalpha():
                continue
            return True
    return False


def _is_meta_question(sentence: str) -> bool:
    folded = normalize(sentence).words.text
    is_question = sentence.rstrip().endswith("?") or bool(_INTERROGATIVE.match(folded))
    return is_question and bool(_META_CUES.search(folded))


def _is_first_person_question(sentence: str) -> bool:
    folded = normalize(sentence).words.text
    is_question = sentence.rstrip().endswith("?") or bool(_INTERROGATIVE.match(folded))
    return is_question and bool(_FIRST_PERSON_Q.search(folded))


def _overlaps(span: tuple[int, int], spans: list[tuple[int, int]]) -> bool:
    return any(span[0] < end and start < span[1] for start, end in spans)


def _signal_findings(signals: list[Signal], original: str) -> list[Finding]:
    by_kind: dict[str, list[Signal]] = {}
    for signal in signals:
        by_kind.setdefault(signal.kind, []).append(signal)
    mapping = {
        "zero_width": "OBF-001",
        "bidi": "OBF-002",
        "tag_char": "OBF-003",
        "mixed_script": "OBF-004",
    }
    findings: list[Finding] = []
    for kind, items in by_kind.items():
        meta = _META_BY_ID[mapping[kind]]
        if kind == "mixed_script":
            for signal in items[:5]:
                findings.append(
                    Finding(
                        meta.id,
                        meta.category,
                        meta.severity,
                        "any",
                        signal.span,
                        _excerpt(original, signal.span),
                        meta.description,
                        layer="raw",
                    )
                )
            continue
        span = (min(s.span[0] for s in items), max(s.span[1] for s in items))  # ein Befund je Art
        findings.append(
            Finding(
                meta.id,
                meta.category,
                meta.severity,
                "any",
                span,
                f"{len(items)} Zeichen",
                meta.description,
                layer="raw",
                notes=(f"count:{len(items)}",),
            )
        )
    return findings


def _adjust_severity(
    rule: Rule,
    context: Context,
    view_name: str,
    original: str,
    span: tuple[int, int],
    meta_text: bool,
    config: EngineConfig,
) -> tuple[Severity, tuple[str, ...]]:
    severity = rule.severity_for(context)
    notes: list[str] = []
    if view_name not in PRIMARY_VIEWS:
        severity = Severity.max(severity, Severity.HIGH)
        notes.append(f"obfuscated:{view_name}")
        return severity, tuple(notes)
    if context is not Context.CHAT:
        return severity, ()
    if config.mention_dampening and rule.mention_dampening != "none":
        sentence = _sentence(original, span)
        if rule.mention_dampening == "meta" and _is_meta_question(sentence):
            severity = severity.shifted(-2)
            notes.append("dampened:meta_question")
        elif rule.mention_dampening == "quoted" and meta_text and _inside_quotes(original, span):
            severity = severity.shifted(-1)
            notes.append("dampened:quoted_mention")
    if config.question_dampening and rule.question_dampening:
        sentence = _sentence(original, span)
        if _is_first_person_question(sentence):
            severity = severity.shifted(-2)
            notes.append("dampened:first_person_question")
    return severity, tuple(notes)


def _rule_findings(norm: Normalized, context: Context, config: EngineConfig) -> list[Finding]:
    original = norm.original
    meta_text = context is Context.CHAT and bool(_META_CUES.search(norm.words.text))
    findings: list[Finding] = []
    for rule in rules_for(context):
        primary_spans: list[tuple[int, int]] = []
        count = 0
        for view_name in rule.views:
            if count >= MAX_FINDINGS_PER_RULE:
                break
            view = norm.view(view_name)
            if view is None or not view.text or not prefilter_passes(rule, view_name, view.text):
                continue
            pattern = compiled_pattern(rule, view_name)
            for match in pattern.finditer(view.text):
                if match.end() <= match.start():
                    continue
                if view.regions and not _overlaps(match.span(), list(view.regions)):
                    continue
                mc = MatchContext(view, match, norm, context)
                if not all(validator(mc) for validator in rule.validators):
                    continue
                span = view.to_original(match.start(), match.end())
                if view_name in PRIMARY_VIEWS:
                    primary_spans.append(span)
                elif _overlaps(span, primary_spans):
                    continue
                severity, notes = _adjust_severity(rule, context, view_name, original, span, meta_text, config)
                findings.append(
                    Finding(
                        rule.id,
                        rule.category,
                        severity,
                        attribute_language(match.group()),
                        span,
                        _excerpt(original, span),
                        rule.description,
                        layer=view_name,
                        notes=notes,
                    )
                )
                count += 1
                if count >= MAX_FINDINGS_PER_RULE:
                    break
    return findings


def _analyze(
    text: str,
    context: Context,
    config: EngineConfig,
    budget: DecodeBudget,
    depth: int,
) -> list[Finding]:
    norm = normalize(text)
    findings = _rule_findings(norm, context, config)
    findings.extend(_signal_findings(norm.signals, text))
    if depth >= config.decode_depth:
        return findings
    for segment in find_encoded_segments(text, budget):
        inner = _analyze(segment.text, context, config, budget, depth + 1)
        for finding in inner:
            if finding.category is Category.RESOURCE_LIMIT:
                continue
            severity = finding.severity
            if finding.category is not Category.OBFUSCATION:
                severity = Severity.max(severity, Severity.HIGH)
            findings.append(
                Finding(
                    finding.rule_id,
                    finding.category,
                    severity,
                    finding.language,
                    segment.span,
                    _excerpt(segment.text, finding.span),
                    finding.description,
                    layer=f"{segment.kind}>{finding.layer}",
                    notes=(*finding.notes, f"decoded:{segment.kind}"),
                )
            )
    return findings


def analyze(text: str, context: Context, config: EngineConfig | None = None) -> tuple[list[Finding], bool]:
    """Prüft ``text`` im angegebenen Kontext.

    Rückgabe: (Befunde sortiert nach Position, ``True`` falls die Eingabe gekürzt wurde).
    """
    config = config or EngineConfig()
    truncated = len(text) > config.max_input_chars
    subject = text[: config.max_input_chars] if truncated else text
    budget = DecodeBudget(
        max_segments=config.max_decoded_segments,
        max_total_chars=config.max_decoded_chars,
    )
    findings = _analyze(subject, context, config, budget, depth=0)
    if truncated:
        meta = _META_BY_ID["LIM-001"]
        findings.append(
            Finding(
                meta.id,
                meta.category,
                meta.severity,
                "any",
                (config.max_input_chars, len(text)),
                f"{len(text)} Zeichen, geprüft: {config.max_input_chars}",
                meta.description,
                layer="raw",
            )
        )
    obfuscated = [
        f
        for f in findings
        if f.category not in (Category.OBFUSCATION, Category.RESOURCE_LIMIT)
        and any(note.startswith(("obfuscated:", "decoded:")) for note in f.notes)
    ]
    if obfuscated:
        meta = _META_BY_ID["OBF-005"]
        first = obfuscated[0]
        findings.append(
            Finding(
                meta.id,
                meta.category,
                meta.severity,
                first.language,
                first.span,
                first.excerpt,
                meta.description,
                layer=first.layer,
                notes=(f"source:{first.rule_id}",),
            )
        )
    if budget.exhausted:
        meta = _META_BY_ID["LIM-002"]
        findings.append(
            Finding(
                meta.id,
                meta.category,
                meta.severity,
                "any",
                (0, 0),
                f"{budget.used_segments} Segmente dekodiert",
                meta.description,
                layer="raw",
            )
        )
    findings.sort(key=lambda f: (f.span[0], f.span[1], f.rule_id))
    return findings, truncated
