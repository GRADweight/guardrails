"""Erkennung und Dekodierung eingebetteter Kodierungen (Base64, Hex, URL, HTML, Unicode).

Die Dekodierung ist bewusst begrenzt: Anzahl Segmente, Länge je Segment und Gesamtmenge sind
gedeckelt, damit ein Angreifer mit verschachtelten Kodierungen keine unbegrenzte Rechenzeit
erzwingen kann (Denial of Service). Die Rekursionstiefe steuert die Engine.

Dekodierte Segmente gelten nur dann als Text, wenn sie gültiges UTF-8 sind und überwiegend aus
druckbaren Zeichen und Buchstaben bestehen. So wird nicht jeder lange Bezeichner, Hash oder
Schlüssel als Klartext weiterverarbeitet.
"""

from __future__ import annotations

import base64
import binascii
import html
import re
import urllib.parse
from collections.abc import Callable, Iterator
from dataclasses import dataclass

__all__ = ["DecodeBudget", "DecodedSegment", "find_encoded_segments"]

_BASE64 = re.compile(r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/_-]{12,}={0,2}(?![A-Za-z0-9+/=_-])")
_HEX_PLAIN = re.compile(r"(?<![0-9A-Za-z])(?:[0-9A-Fa-f]{2}){6,}(?![0-9A-Za-z])")
_HEX_ESCAPED = re.compile(r"(?:\\x[0-9A-Fa-f]{2}){4,}")
_HEX_SEPARATED = re.compile(r"(?<![0-9A-Za-z])(?:0x)?[0-9A-Fa-f]{2}(?:[ :,-](?:0x)?[0-9A-Fa-f]{2}){5,}(?![0-9A-Za-z])")
_TOKEN = re.compile(r"\S+")
_PERCENT = re.compile(r"%[0-9A-Fa-f]{2}")
_HTML = re.compile(r"(?:&(?:#\d{1,7}|#[xX][0-9A-Fa-f]{1,6}|[A-Za-z]{2,8});[^&<>]{0,2}){3,}")
_UESCAPE = re.compile(r"(?:\\u[0-9A-Fa-f]{4}){3,}")
_TAGS = re.compile("[\U000e0020-\U000e007e]{4,}")


@dataclass(frozen=True, slots=True)
class DecodedSegment:
    """Ein dekodiertes Segment. ``span`` bezieht sich auf den Text, in dem es gefunden wurde."""

    kind: str
    span: tuple[int, int]
    text: str


@dataclass(slots=True)
class DecodeBudget:
    """Gemeinsames Budget für alle Rekursionsstufen einer Prüfung."""

    max_segments: int = 16
    max_segment_chars: int = 8192
    max_total_chars: int = 65536
    used_segments: int = 0
    used_chars: int = 0
    exhausted: bool = False

    def take(self, size: int) -> bool:
        if self.used_segments >= self.max_segments or self.used_chars + size > self.max_total_chars:
            self.exhausted = True
            return False
        self.used_segments += 1
        self.used_chars += size
        return True


def _plausible_text(text: str) -> bool:
    """True, wenn ``text`` wie natürlichsprachlicher oder Befehls-Text aussieht."""
    if len(text) < 4:
        return False
    printable = sum(1 for c in text if c.isprintable() or c in "\n\t")
    if printable / len(text) < 0.95:
        return False
    letters = sum(1 for c in text if c.isalpha() or c == " ")
    return letters / len(text) >= 0.5


def _decode_bytes(raw: bytes) -> str | None:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return text if _plausible_text(text) else None


def _try_base64(candidate: str) -> str | None:
    core = candidate.rstrip("=")
    has_upper = any(c.isupper() for c in core)
    has_lower = any(c.islower() for c in core)
    has_other = any(c.isdigit() or c in "+/_-" for c in core)
    if not ((has_upper and has_lower) or has_other):
        return None
    if len(core) % 4 == 1:
        return None
    standard = core.replace("-", "+").replace("_", "/")
    padded = standard + "=" * (-len(standard) % 4)
    try:
        raw = base64.b64decode(padded, validate=True)
    except (binascii.Error, ValueError):
        return None
    return _decode_bytes(raw)


def _try_hex(candidate: str) -> str | None:
    digits = re.sub(r"\\x|0x|[ :,-]", "", candidate)
    if len(digits) % 2:
        return None
    try:
        raw = bytes.fromhex(digits)
    except ValueError:
        return None
    return _decode_bytes(raw)


def _try_url(candidate: str) -> str | None:
    try:
        decoded = urllib.parse.unquote_plus(candidate, errors="strict")
    except UnicodeDecodeError:
        return None
    if decoded == candidate:
        return None
    return decoded if _plausible_text(decoded) else None


def _try_html(candidate: str) -> str | None:
    decoded = html.unescape(candidate)
    return decoded if decoded != candidate and _plausible_text(decoded) else None


def _try_uescape(candidate: str) -> str | None:
    decoded = re.sub(r"\\u([0-9A-Fa-f]{4})", lambda m: chr(int(m.group(1), 16)), candidate)
    return decoded if _plausible_text(decoded) else None


def _try_tags(candidate: str) -> str | None:
    decoded = "".join(chr(ord(c) - 0xE0000) for c in candidate)
    return decoded if _plausible_text(decoded) else None


_DECODERS = (
    ("unicode_tags", _TAGS, _try_tags),
    ("base64", _BASE64, _try_base64),
    ("hex", _HEX_ESCAPED, _try_hex),
    ("hex", _HEX_SEPARATED, _try_hex),
    ("hex", _HEX_PLAIN, _try_hex),
    ("html", _HTML, _try_html),
    ("unicode_escape", _UESCAPE, _try_uescape),
)


def _url_candidates(text: str) -> Iterator[re.Match[str]]:
    """Tokens mit mindestens drei %XX-Sequenzen (linear; ein Regex über ganze Tokens wäre quadratisch)."""
    for match in _TOKEN.finditer(text):
        token = match.group()
        if token.count("%") >= 3 and len(_PERCENT.findall(token)) >= 3:
            yield match


def find_encoded_segments(text: str, budget: DecodeBudget) -> list[DecodedSegment]:
    """Sucht kodierte Segmente in ``text`` und dekodiert sie im Rahmen von ``budget``."""
    segments: list[DecodedSegment] = []
    covered: list[tuple[int, int]] = []
    sources: list[tuple[str, Iterator[re.Match[str]], Callable[[str], str | None]]] = [
        (kind, pattern.finditer(text), decoder) for kind, pattern, decoder in _DECODERS
    ]
    sources.insert(5, ("url", _url_candidates(text), _try_url))
    for kind, matches, decoder in sources:
        for match in matches:
            start, end = match.span()
            if any(start < c_end and c_start < end for c_start, c_end in covered):
                continue
            candidate = match.group()
            if len(candidate) > budget.max_segment_chars:
                candidate = candidate[: budget.max_segment_chars]
            decoded = decoder(candidate)
            if decoded is None:
                continue
            if not budget.take(len(decoded)):
                return segments
            segments.append(DecodedSegment(kind, (start, end), decoded))
            covered.append((start, end))
    return segments
