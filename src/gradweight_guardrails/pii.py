"""Erkennung und Schwärzung von Personendaten mit Prüfziffern (Schweizer Schwerpunkt).

* AHV-Nummer (AHVN13): 756.XXXX.XXXX.XP, Prüfziffer nach EAN-13 (Gewichte 1/3 von links).
* IBAN: Länge je Land (u.a. CH und LI je 21 Stellen) und Prüfsumme modulo 97 (ISO 13616).
* Kreditkartennummern: 13–19 Ziffern, Luhn-Prüfsumme und plausible Kartenpräfixe.
* E-Mail-Adressen und Schweizer Telefonnummern (+41/0041/0 und neun nationale Ziffern).

Grenzen: Telefonnummern und E-Mail-Adressen haben keine Prüfziffer und werden nur nach Form
erkannt. Namen, Adressen und Geburtsdaten werden nicht erkannt.
"""

from __future__ import annotations

import enum
import re
from collections.abc import Iterable
from dataclasses import dataclass

__all__ = ["PiiKind", "PiiMatch", "ahv_valid", "find_pii", "iban_valid", "luhn_valid", "redact_pii"]


class PiiKind(enum.StrEnum):
    AHV = "ahv"
    IBAN = "iban"
    CREDIT_CARD = "credit_card"
    EMAIL = "email"
    PHONE_CH = "phone_ch"


@dataclass(frozen=True, slots=True)
class PiiMatch:
    """Fundstelle. ``valid`` ist True, wenn die Prüfziffer stimmt (bei E-Mail/Telefon: Form)."""

    kind: PiiKind
    span: tuple[int, int]
    value: str
    valid: bool


# IBAN-Längen je Land (SWIFT IBAN Registry), Auswahl Europa.
IBAN_LENGTHS: dict[str, int] = {
    "AD": 24, "AT": 20, "BE": 16, "BG": 22, "CH": 21, "CY": 28, "CZ": 24, "DE": 22, "DK": 18,
    "EE": 20, "ES": 24, "FI": 18, "FR": 27, "GB": 22, "GI": 23, "GR": 27, "HR": 21, "HU": 28,
    "IE": 22, "IS": 26, "IT": 27, "LI": 21, "LT": 20, "LU": 20, "LV": 21, "MC": 27, "MT": 31,
    "NL": 18, "NO": 15, "PL": 28, "PT": 25, "RO": 24, "SE": 24, "SI": 19, "SK": 24, "SM": 27,
    "VA": 22,
}  # fmt: skip

_AHV = re.compile(r"(?<!\d)756[.\s -]?\d{4}[.\s -]?\d{4}[.\s -]?\d{2}(?!\d)")
_IBAN = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]{2}\d{2}(?:[  ]?[A-Za-z0-9]){11,32}")
_CARD = re.compile(r"(?<![\d-])\d(?:[ -]?\d){12,18}(?![\d-])")
_EMAIL = re.compile(r"(?<![\w.+-])[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9-]{1,63}(?:\.[A-Za-z0-9-]{1,63})*\.[A-Za-z]{2,24}\b")
_PHONE = re.compile(r"(?<![\d+])(?:\+41|0041|0)[  .\-/]?(?:\(0\)[  ]?)?[1-9]\d(?:[  .\-/]?\d){7}(?!\d)")


def _digits(value: str) -> str:
    return "".join(c for c in value if c.isdigit())


def ahv_valid(value: str) -> bool:
    """Prüft eine AHV-Nummer (13 Ziffern, Präfix 756, EAN-13-Prüfziffer)."""
    digits = _digits(value)
    if len(digits) != 13 or not digits.startswith("756"):
        return False
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(digits[:12]))
    return (10 - total % 10) % 10 == int(digits[12])


def iban_valid(value: str) -> bool:
    """Prüft eine IBAN (Länge je Land, falls bekannt, und Prüfsumme modulo 97)."""
    iban = re.sub(r"\s", "", value).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", iban):
        return False
    expected = IBAN_LENGTHS.get(iban[:2])
    if expected is not None and len(iban) != expected:
        return False
    rearranged = iban[4:] + iban[:4]
    numeric = "".join(str(int(c, 36)) for c in rearranged)
    return int(numeric) % 97 == 1


def luhn_valid(value: str) -> bool:
    """Prüft die Luhn-Prüfsumme einer Ziffernfolge (13–19 Stellen)."""
    digits = _digits(value)
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d)
        if i % 2:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _card_prefix_plausible(digits: str) -> bool:
    if digits[0] == "4":
        return True
    two = int(digits[:2])
    four = int(digits[:4])
    return (
        51 <= two <= 55
        or 2221 <= four <= 2720
        or two in (34, 37, 36, 38, 39, 65, 62)
        or 300 <= int(digits[:3]) <= 305
        or digits.startswith("6011")
        or 644 <= int(digits[:3]) <= 649
        or 3528 <= four <= 3589
        or two in (50, 56, 57, 58, 63, 67)
    )


def _iban_candidates(text: str) -> Iterable[tuple[tuple[int, int], str]]:
    position = 0
    while True:
        match = _IBAN.search(text, position)
        if match is None:
            return
        raw = match.group()
        expected = IBAN_LENGTHS.get(raw[:2].upper())
        limit = expected if expected is not None else 34
        compact_len = 0
        end = match.start()
        for offset, c in enumerate(raw):
            if c.isalnum():
                compact_len += 1
                end = match.start() + offset + 1
                if compact_len == limit:
                    break
        if expected is None or compact_len == expected:
            yield (match.start(), end), text[match.start() : end]
            position = end
        else:
            position = match.start() + 1


def _overlaps(span: tuple[int, int], taken: list[tuple[int, int]]) -> bool:
    return any(span[0] < e and s < span[1] for s, e in taken)


def find_pii(
    text: str,
    *,
    kinds: Iterable[PiiKind] | None = None,
    require_valid: bool = True,
) -> list[PiiMatch]:
    """Findet Personendaten. Mit ``require_valid`` nur Treffer mit gültiger Prüfziffer."""
    wanted = set(kinds) if kinds is not None else set(PiiKind)
    found: list[PiiMatch] = []
    taken: list[tuple[int, int]] = []

    def add(kind: PiiKind, span: tuple[int, int], valid: bool) -> None:
        if require_valid and not valid:
            return
        if _overlaps(span, taken):
            return
        taken.append(span)
        found.append(PiiMatch(kind, span, text[span[0] : span[1]], valid))

    # Reihenfolge wichtig: Nummern mit Prüfziffer zuerst, damit sie nicht als Telefon/Karte gelten.
    for match in _AHV.finditer(text):
        valid = ahv_valid(match.group())
        if PiiKind.AHV in wanted:
            add(PiiKind.AHV, match.span(), valid)
        elif valid:
            taken.append(match.span())
    for span, value in _iban_candidates(text):
        valid = iban_valid(value)
        if PiiKind.IBAN in wanted:
            add(PiiKind.IBAN, span, valid)
        elif valid:
            taken.append(span)
    if PiiKind.CREDIT_CARD in wanted:
        for match in _CARD.finditer(text):
            digits = _digits(match.group())
            add(
                PiiKind.CREDIT_CARD,
                match.span(),
                luhn_valid(digits) and _card_prefix_plausible(digits),
            )
    if PiiKind.EMAIL in wanted:
        for match in _EMAIL.finditer(text):
            add(PiiKind.EMAIL, match.span(), True)
    if PiiKind.PHONE_CH in wanted:
        for match in _PHONE.finditer(text):
            digits = _digits(match.group().replace("(0)", ""))
            national = (
                digits[2:] if digits.startswith("41") else digits[4:] if digits.startswith("0041") else digits[1:]
            )
            add(PiiKind.PHONE_CH, match.span(), len(national) == 9)
    found.sort(key=lambda m: m.span)
    return found


def redact_pii(
    text: str,
    *,
    kinds: Iterable[PiiKind] | None = None,
    require_valid: bool = True,
    template: str = "[{kind}]",
) -> tuple[str, list[PiiMatch]]:
    """Ersetzt gefundene Personendaten durch ``template`` (Platzhalter ``{kind}``)."""
    matches = find_pii(text, kinds=kinds, require_valid=require_valid)
    out = text
    for match in sorted(matches, key=lambda m: m.span[0], reverse=True):
        replacement = template.format(kind=match.kind.value.upper())
        out = out[: match.span[0]] + replacement + out[match.span[1] :]
    return out, matches
