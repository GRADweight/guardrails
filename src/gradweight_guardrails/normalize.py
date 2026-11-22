"""Normalisierung: mehrere Sichten auf denselben Text, jede mit Rückabbildung auf das Original.

Erkennungsregeln laufen nicht auf dem Rohtext, sondern auf normalisierten Sichten. Jede Sicht
führt eine Indexliste, die für jedes Zeichen die Position im Originaltext enthält. Damit
lassen sich Treffer immer auf den Originaltext zurückführen.

Sichten:

``text``
    Unicode-NFKD, diakritische Zeichen und unsichtbare Formatzeichen entfernt, casefold,
    kyrillische und griechische Doppelgänger auf lateinische Buchstaben abgebildet,
    Leerraum zusammengefasst (Zeilenumbrüche bleiben als ``\\n`` erhalten).
``words``
    wie ``text``, aber alle Zeichen ausser Buchstaben und Ziffern werden zu einem Leerzeichen.
``leet``
    wie ``words``, nachdem Leetspeak in Wörtern mit Buchstaben aufgelöst wurde (``1gn0r3``).
    Nur vorhanden, wenn der Text solche Wörter enthält.
``compact``
    wie ``words``, mit aufgehobener Sperrschrift (``i g n o r e`` → ``ignore``).
    Nur vorhanden, wenn mindestens drei einzelne Zeichen hintereinander stehen.
``typo``
    wie ``words``, Buchstabendreher in Schlüsselwörtern korrigiert (``Igonriere`` → ``ignoriere``):
    ein Wort, das ein Anagramm eines Schlüsselworts mit gleichem Anfangsbuchstaben ist.
``rejoin``
    wie ``words``, zerteilte Schlüsselwörter zusammengefügt (``prev ious`` → ``previous``).
``rot13`` / ``reversed``
    ROT13-dekodierte bzw. rückwärts gelesene ``words``-Sicht. Nur vorhanden, wenn ein
    Abschnitt des Textes kaum gewöhnliche Funktionswörter enthält (Hinweis auf Kodierung).
"""

from __future__ import annotations

import codecs
import functools
import re
import unicodedata
from dataclasses import dataclass

from .lexicon import KEY_WORDS

__all__ = ["Normalized", "Signal", "View", "fold", "normalize"]

# Kyrillische und griechische Zeichen, die lateinischen Buchstaben zum Verwechseln ähnlich sind
# (nach casefold). Quelle: Unicode confusables, auf die häufigsten Fälle beschränkt.
_HOMOGLYPHS: dict[str, str] = {
    # Kyrillisch
    "а": "a",
    "в": "b",
    "е": "e",
    "ё": "e",
    "і": "i",
    "ї": "i",
    "ј": "j",
    "к": "k",
    "м": "m",
    "н": "h",
    "о": "o",
    "р": "p",
    "с": "c",
    "т": "t",
    "у": "y",
    "х": "x",
    "ѕ": "s",
    "ԁ": "d",
    "һ": "h",
    "ӏ": "l",
    "ԛ": "q",
    "ԝ": "w",
    "ү": "y",
    # Griechisch
    "α": "a",
    "β": "b",
    "ε": "e",
    "η": "n",
    "ι": "i",
    "κ": "k",
    "ν": "v",
    "ο": "o",
    "ρ": "p",
    "τ": "t",
    "υ": "u",
    "χ": "x",
    "ω": "w",
    "ϲ": "c",
    "ϳ": "j",
    # Typografische Apostrophe (für Elisionen wie l’IA, all’utente)
    "\u2019": "'",
    "\u2018": "'",
    "\u02bc": "'",
    "\uff07": "'",
    # Lateinische Sonderformen
    "ı": "i",
    "ɡ": "g",
    "ʏ": "y",
    "ℓ": "l",
}

_LINE_BREAKS = frozenset("\n\r\x0b\x0c\x85  ")
# Unsichtbare Zeichen, die nicht in der Unicode-Kategorie Cf liegen.
_EXTRA_INVISIBLE = frozenset({0x115F, 0x1160, 0x3164, 0xFFA0, 0x180E})
_BIDI = frozenset({0x200E, 0x200F, 0x061C, *range(0x202A, 0x202F), *range(0x2066, 0x206A)})
_ZERO_WIDTH = frozenset({0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF})

_LEET = {
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "8": "b",
    "@": "a",
    "$": "s",
    "!": "i",
    "|": "i",
    "€": "e",
}
_LEET_TRAILING = ".,;:?!)]}\"'»”’…"
_LEET_LEADING = "([{\"'«„“‘"

_STOPWORDS = frozenset(
    """
    the a an and or of to in on for is are was be it this that with as at by from i you we my your
    me do not can please what how der die das und oder ist sind ein eine einen ich du wir sie es
    nicht mit von zu im auf fur den dem des bitte wie was mir mein dein le la les un une des et ou
    est sont je tu nous vous il elle de du en dans pour sur pas ne que qui avec ce cette mon ton il
    lo gli e o di da con su per non che mi ti sono io noi questo questa mio tuo del della
    """.split()
)

_SINGLE_CHAR_RUN = re.compile(r"(?<!\S)\S(?: \S){2,}(?!\S)")
_SEGMENT_SPLIT = re.compile(r"[.!?:;\n]+")


@functools.lru_cache(maxsize=16384)
def _fold_char(ch: str) -> str:
    """Faltet ein einzelnes Zeichen. Leerer String bedeutet: Zeichen entfernen."""
    if ch in _LINE_BREAKS:
        return "\n"
    if ch.isspace():
        return " "
    cp = ord(ch)
    if cp in _EXTRA_INVISIBLE:
        return ""
    category = unicodedata.category(ch)
    if category == "Cf":
        return ""
    if category == "Cc":
        return " "
    out: list[str] = []
    for part in unicodedata.normalize("NFKD", ch):
        if unicodedata.category(part) == "Mn":
            continue
        for folded in part.casefold():
            out.append(_HOMOGLYPHS.get(folded, folded))
    return "".join(out)


def fold(text: str) -> str:
    """Faltet einen Text wie die ``text``-Sicht, ohne Indexliste (für Hilfsprüfungen)."""
    return normalize(text).text.text


@dataclass(frozen=True, slots=True, eq=False)
class View:
    """Eine Sicht auf den Text. ``index[i]`` ist die Originalposition von ``text[i]``."""

    name: str
    text: str
    index: list[int]
    regions: tuple[tuple[int, int], ...] = ()
    """Bereiche (in Koordinaten dieser Sicht), die durch eine Entschleierung entstanden sind."""

    def to_original(self, start: int, end: int) -> tuple[int, int]:
        """Bildet den Bereich ``[start, end)`` dieser Sicht auf den Originaltext ab."""
        if not self.index or end <= start:
            return (0, 0)
        last = len(self.index) - 1
        a = self.index[min(max(start, 0), last)]
        b = self.index[min(max(end - 1, 0), last)]
        return (min(a, b), max(a, b) + 1)


@dataclass(frozen=True, slots=True)
class Signal:
    """Hinweis auf Verschleierung, gefunden bei der Normalisierung."""

    kind: str
    span: tuple[int, int]


def _build_text_view(original: str) -> View:
    out: list[str] = []
    index: list[int] = []
    pending: str | None = None
    pending_index = 0
    for position, ch in enumerate(original):
        folded = _fold_char(ch)
        if not folded:
            continue
        for c in folded:
            if c in (" ", "\n"):
                if pending is None:
                    pending, pending_index = c, position
                elif c == "\n":
                    pending = "\n"
                continue
            if pending is not None and out:
                out.append(pending)
                index.append(pending_index)
            pending = None
            out.append(c)
            index.append(position)
    return View("text", "".join(out), index)


def _words_from(source: View, name: str) -> View:
    out: list[str] = []
    index: list[int] = []
    pending = False
    pending_index = 0
    for c, position in zip(source.text, source.index, strict=True):
        if c.isalnum():
            if pending and out:
                out.append(" ")
                index.append(pending_index)
            pending = False
            out.append(c)
            index.append(position)
        elif not pending:
            pending = True
            pending_index = position
    return View(name, "".join(out), index)


def _leet_text(text_view: View) -> View | None:
    chars = list(text_view.text)
    changed = False
    for match in re.finditer(r"\S+", text_view.text):
        token = match.group()
        start = match.start()
        lead = len(token) - len(token.lstrip(_LEET_LEADING))
        core_end = len(token.rstrip(_LEET_TRAILING))
        core = token[lead:core_end]
        if not core or not any("a" <= c <= "z" for c in core):
            continue
        if not any(c in _LEET for c in core):
            continue
        for offset, c in enumerate(core):
            mapped = _LEET.get(c)
            if mapped is not None:
                chars[start + lead + offset] = mapped
                changed = True
    if not changed:
        return None
    return _words_from(View("leet_text", "".join(chars), text_view.index), "leet")


MAX_COMPACT_CHARS = 4000
"""Obergrenze für entschleierte Sperrschrift je Text (begrenzt die Laufzeit der compact-Muster)."""


def _compact_from(words: View) -> View | None:
    runs: list[re.Match[str]] = []
    budget = MAX_COMPACT_CHARS
    for run in _SINGLE_CHAR_RUN.finditer(words.text):
        size = run.end() - run.start()
        if size > budget:
            break
        budget -= size
        runs.append(run)
    if not runs:
        return None
    pieces: list[str] = []
    index: list[int] = []
    regions: list[tuple[int, int]] = []
    cursor = 0
    for run in runs:
        pieces.append(words.text[cursor : run.start()])
        index.extend(words.index[cursor : run.start()])
        region_start = len(index)
        for offset in range(run.start(), run.end()):
            if words.text[offset] != " ":
                pieces.append(words.text[offset])
                index.append(words.index[offset])
        regions.append((region_start, len(index)))
        cursor = run.end()
    pieces.append(words.text[cursor:])
    index.extend(words.index[cursor:])
    return View("compact", "".join(pieces), index, tuple(regions))


def _anagram_key(word: str) -> tuple[str, str]:
    return (word[0], "".join(sorted(word)))


_ANAGRAMS: dict[tuple[str, str], str] = {}
for _word in sorted(KEY_WORDS):
    _ANAGRAMS.setdefault(_anagram_key(_word), _word)


def _typo_from(words: View) -> View | None:
    """Ersetzt Wörter, die Anagramme eines Schlüsselworts sind, durch das Schlüsselwort."""
    pieces: list[str] = []
    index: list[int] = []
    regions: list[tuple[int, int]] = []
    cursor = 0
    for match in re.finditer(r"[^\W\d_]{5,}", words.text):
        token = match.group()
        if token in KEY_WORDS:
            continue
        replacement = _ANAGRAMS.get(_anagram_key(token))
        if replacement is None:
            continue
        pieces.append(words.text[cursor : match.start()])
        index.extend(words.index[cursor : match.start()])
        start = len(index)
        pieces.append(replacement)
        index.extend(words.index[match.start() : match.end()])
        regions.append((start, len(index)))
        cursor = match.end()
    if not regions:
        return None
    pieces.append(words.text[cursor:])
    index.extend(words.index[cursor:])
    return View("typo", "".join(pieces), index, tuple(regions))


def _rejoin_from(words: View) -> View | None:
    """Fügt zwei oder drei benachbarte Wortteile zusammen, wenn sie ein Schlüsselwort ergeben."""
    spans = [(m.start(), m.end()) for m in re.finditer(r"\S+", words.text)]
    tokens = [words.text[s:e] for s, e in spans]
    pieces: list[str] = []
    index: list[int] = []
    regions: list[tuple[int, int]] = []
    i = 0
    cursor = 0
    while i < len(tokens):
        joined = None
        for width in (3, 2):
            if i + width > len(tokens):
                continue
            parts = tokens[i : i + width]
            candidate = "".join(parts)
            if candidate in KEY_WORDS and not all(part in KEY_WORDS for part in parts):
                joined = (width, candidate)
                break
        if joined is None:
            i += 1
            continue
        width, candidate = joined
        start_char, end_char = spans[i][0], spans[i + width - 1][1]
        pieces.append(words.text[cursor:start_char])
        index.extend(words.index[cursor:start_char])
        region_start = len(index)
        for k in range(i, i + width):
            s, e = spans[k]
            pieces.append(words.text[s:e])
            index.extend(words.index[s:e])
        regions.append((region_start, len(index)))
        cursor = end_char
        i += width
    if not regions:
        return None
    pieces.append(words.text[cursor:])
    index.extend(words.index[cursor:])
    return View("rejoin", "".join(pieces), index, tuple(regions))


def _looks_encoded(text_view: View) -> bool:
    """True, wenn ein Abschnitt kaum Funktionswörter enthält (möglicher ROT13- oder Rückwärtstext)."""
    for segment in _SEGMENT_SPLIT.split(text_view.text):
        tokens = re.findall(r"[^\W\d_]{2,}", segment)
        if len(tokens) < 3:
            continue
        stop = sum(1 for t in tokens if t in _STOPWORDS)
        if stop / len(tokens) < 0.12:
            return True
    return False


_SCRIPT_CACHE: dict[str, str] = {}


def _script_of(ch: str) -> str:
    cached = _SCRIPT_CACHE.get(ch)
    if cached is not None:
        return cached
    name = unicodedata.name(ch, "")
    script = "other"
    for candidate in ("LATIN", "CYRILLIC", "GREEK"):
        if name.startswith(candidate):
            script = candidate
            break
    if len(_SCRIPT_CACHE) < 8192:
        _SCRIPT_CACHE[ch] = script
    return script


def _collect_signals(original: str) -> list[Signal]:
    signals: list[Signal] = []
    length = len(original)
    in_flag_sequence = False
    for position, ch in enumerate(original):
        cp = ord(ch)
        if cp < 0x061C:
            in_flag_sequence = False
            continue
        if cp == 0x1F3F4:
            # Schwarze Flagge: es folgen legitime Tag-Zeichen (z.B. Flagge von Schottland).
            in_flag_sequence = True
            continue
        if 0xE0000 <= cp <= 0xE007F:
            if not in_flag_sequence:
                signals.append(Signal("tag_char", (position, position + 1)))
            continue
        in_flag_sequence = False
        if cp in _ZERO_WIDTH:
            before = original[position - 1] if position > 0 else ""
            after = original[position + 1] if position + 1 < length else ""
            if before.isalnum() and after.isalnum():
                signals.append(Signal("zero_width", (position, position + 1)))
        elif cp in _BIDI:
            signals.append(Signal("bidi", (position, position + 1)))
    if not original.isascii():
        for match in re.finditer(r"[^\W\d_]{2,}", original):
            token = match.group()
            if token.isascii():
                continue
            scripts = {_script_of(c) for c in token} - {"other"}
            if len(scripts) > 1:
                signals.append(Signal("mixed_script", match.span()))
    return signals


class Normalized:
    """Alle Sichten auf einen Text. Teure Sichten werden erst bei Bedarf berechnet."""

    __slots__ = (
        "_compact",
        "_leet",
        "_rejoin",
        "_reversed",
        "_rot13",
        "_signals",
        "_transforms_checked",
        "_typo",
        "original",
        "text",
        "words",
    )

    def __init__(self, original: str) -> None:
        self.original = original
        self.text = _build_text_view(original)
        self.words = _words_from(self.text, "words")
        self._leet: View | bool | None = False
        self._compact: View | bool | None = False
        self._typo: View | bool | None = False
        self._rejoin: View | bool | None = False
        self._rot13: View | None = None
        self._reversed: View | None = None
        self._transforms_checked = False
        self._signals: list[Signal] | None = None

    @property
    def leet(self) -> View | None:
        if self._leet is False:
            self._leet = _leet_text(self.text)
        return self._leet if isinstance(self._leet, View) else None

    @property
    def compact(self) -> View | None:
        if self._compact is False:
            self._compact = _compact_from(self.words)
        return self._compact if isinstance(self._compact, View) else None

    @property
    def typo(self) -> View | None:
        if self._typo is False:
            self._typo = _typo_from(self.words)
        return self._typo if isinstance(self._typo, View) else None

    @property
    def rejoin(self) -> View | None:
        if self._rejoin is False:
            self._rejoin = _rejoin_from(self.words)
        return self._rejoin if isinstance(self._rejoin, View) else None

    def _ensure_transforms(self) -> None:
        if self._transforms_checked:
            return
        self._transforms_checked = True
        if _looks_encoded(self.text):
            words = self.words
            self._rot13 = View("rot13", codecs.encode(words.text, "rot13"), words.index)
            self._reversed = View("reversed", words.text[::-1], words.index[::-1])

    @property
    def rot13(self) -> View | None:
        self._ensure_transforms()
        return self._rot13

    @property
    def reversed(self) -> View | None:
        self._ensure_transforms()
        return self._reversed

    @property
    def signals(self) -> list[Signal]:
        if self._signals is None:
            self._signals = _collect_signals(self.original)
        return self._signals

    def view(self, name: str) -> View | None:
        """Gibt die Sicht mit dem Namen ``name`` zurück (oder None, falls nicht vorhanden)."""
        if name == "text":
            return self.text
        if name == "words":
            return self.words
        if name == "leet":
            return self.leet
        if name == "compact":
            return self.compact
        if name == "typo":
            return self.typo
        if name == "rejoin":
            return self.rejoin
        if name == "rot13":
            return self.rot13
        if name == "reversed":
            return self.reversed
        raise ValueError(f"Unbekannte Sicht: {name!r}")


def normalize(text: str) -> Normalized:
    """Erzeugt alle Sichten für ``text``."""
    return Normalized(text)
