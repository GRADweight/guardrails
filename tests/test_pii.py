"""Personendaten mit Prüfziffern. Testwerte sind öffentliche Beispielnummern."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from gradweight_guardrails import PiiKind, find_pii, redact_pii
from gradweight_guardrails.pii import IBAN_LENGTHS, ahv_valid, iban_valid, luhn_valid

AHV_EXAMPLE = "756.1234.5678.97"  # Beispiel aus der Dokumentation der ZAS
IBAN_CH = "CH93 0076 2011 6238 5295 7"
IBAN_LI = "LI21 0881 0000 2324 013A A"
IBAN_DE = "DE89 3704 0044 0532 0130 00"
VISA_TEST = "4111 1111 1111 1111"


def test_ahv() -> None:
    assert ahv_valid(AHV_EXAMPLE)
    assert ahv_valid("7561234567897")
    assert not ahv_valid("756.1234.5678.98")
    assert not ahv_valid("123.1234.5678.97")


@pytest.mark.parametrize("iban", [IBAN_CH, IBAN_LI, IBAN_DE, "ch9300762011623852957"])
def test_iban_valid(iban: str) -> None:
    assert iban_valid(iban)


@pytest.mark.parametrize("iban", ["CH93 0076 2011 6238 5295 8", "CH93 0076 2011 6238 5295", "XX12", "DE89"])
def test_iban_invalid(iban: str) -> None:
    assert not iban_valid(iban)


def test_luhn() -> None:
    assert luhn_valid(VISA_TEST)
    assert luhn_valid("5555 5555 5555 4444")
    assert luhn_valid("3782 822463 10005")
    assert not luhn_valid("4111 1111 1111 1112")
    assert not luhn_valid("411")


def _ean13_digit(first12: str) -> str:
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(first12))
    return str((10 - total % 10) % 10)


@given(st.text(alphabet="0123456789", min_size=9, max_size=9))
def test_ahv_property_single_digit_errors_detected(body: str) -> None:
    number = "756" + body
    number += _ean13_digit(number)
    assert ahv_valid(number)
    position = 5
    wrong = number[:position] + str((int(number[position]) + 1) % 10) + number[position + 1 :]
    assert not ahv_valid(wrong)


def _iban_with_check(country: str, bban: str) -> str:
    rearranged = bban + country + "00"
    numeric = "".join(str(int(c, 36)) for c in rearranged)
    check = 98 - int(numeric) % 97
    return f"{country}{check:02d}{bban}"


@given(st.text(alphabet="0123456789", min_size=17, max_size=17))
def test_iban_property_mod97(bban: str) -> None:
    iban = _iban_with_check("CH", bban)
    assert len(iban) == IBAN_LENGTHS["CH"]
    assert iban_valid(iban)
    swapped = iban[:5] + str((int(iban[5]) + 1) % 10) + iban[6:]
    assert not iban_valid(swapped)


@given(st.text(alphabet="0123456789", min_size=15, max_size=15))
def test_luhn_property(body: str) -> None:
    number = "4" + body
    for check in "0123456789":
        if luhn_valid(number + check):
            break
    else:  # pragma: no cover - mathematisch ausgeschlossen
        pytest.fail("keine Prüfziffer gefunden")
    valid = number + check
    changed = valid[:-1] + str((int(check) + 1) % 10)
    assert not luhn_valid(changed)


TEXT = (
    f"Max Muster, AHV {AHV_EXAMPLE}, IBAN {IBAN_CH} und {IBAN_LI}, Karte {VISA_TEST}, "
    "Tel. +41 44 123 45 67 oder 079 123 45 67, max.muster@example.ch, Bestellnr. 1234567890123."
)


def test_find_all_kinds() -> None:
    kinds = [m.kind for m in find_pii(TEXT)]
    assert kinds == [
        PiiKind.AHV,
        PiiKind.IBAN,
        PiiKind.IBAN,
        PiiKind.CREDIT_CARD,
        PiiKind.PHONE_CH,
        PiiKind.PHONE_CH,
        PiiKind.EMAIL,
    ]


def test_redaction() -> None:
    redacted, matches = redact_pii(TEXT)
    assert "756.1234" not in redacted
    assert "[AHV]" in redacted
    assert redacted.count("[IBAN]") == 2
    assert "[CREDIT_CARD]" in redacted
    assert "[EMAIL]" in redacted
    assert "1234567890123" in redacted, "ungültige Nummer ohne Prüfziffer bleibt stehen"
    assert len(matches) == 7


def test_redaction_options() -> None:
    redacted, _ = redact_pii(TEXT, kinds=[PiiKind.EMAIL], template="<{kind}>")
    assert "<EMAIL>" in redacted
    assert AHV_EXAMPLE in redacted
    invalid = find_pii("Karte 4111 1111 1111 1112", require_valid=False)
    assert invalid[0].kind is PiiKind.CREDIT_CARD
    assert not invalid[0].valid
    assert find_pii("Karte 4111 1111 1111 1112") == []


def test_iban_not_taken_as_card_or_phone() -> None:
    kinds = {m.kind for m in find_pii(f"IBAN {IBAN_CH}", kinds=[PiiKind.CREDIT_CARD, PiiKind.PHONE_CH])}
    assert kinds == set()


def test_phone_variants() -> None:
    for number in ("+41 79 123 45 67", "0041791234567", "044/123 45 67", "+41 (0)44 123 45 67"):
        assert [m.kind for m in find_pii(number)] == [PiiKind.PHONE_CH], number
