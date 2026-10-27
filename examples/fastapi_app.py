"""Beispiel: Guard als Prüfschritt in einer FastAPI-Anwendung.

Start (nach ``pip install "gradweight-guardrails" fastapi uvicorn``)::

    uvicorn examples.fastapi_app:app --port 8000

Der Endpunkt ``/chat`` prüft die Eingabe, ruft danach das Modell auf (hier eine Attrappe)
und prüft die Antwort mit dem Output-Guard. REVIEW wird hier wie BLOCK behandelt; in einer
echten Anwendung kann REVIEW an einen Menschen oder einen LLM-Judge gehen.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from gradweight_guardrails import AuditEvent, Canary, Decision, Guard, OutputGuard

logger = logging.getLogger("guardrails.audit")

SYSTEM_PROMPT = "Du bist der Support-Assistent der Muster AG. Antworte knapp und sachlich."
CANARY = Canary.generate()


def audit(event: AuditEvent) -> None:
    # Enthält keinen Klartext, nur Hash, Länge, Entscheidung und Regel-IDs.
    logger.info("guard %s %s %s", event.decision, event.rule_ids, event.input_sha256[:12])


guard = Guard(audit=audit)
output_guard = OutputGuard(canaries=[CANARY], system_prompt=SYSTEM_PROMPT)
app = FastAPI(title="Guardrails-Beispiel")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    decision: str


def call_model(system_prompt: str, message: str) -> str:
    """Attrappe für den eigentlichen LLM-Aufruf."""
    return f"Danke für Ihre Nachricht ({len(message)} Zeichen). Kontakt: support@muster-ag.example"


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    verdict = guard.scan(request.message)
    if verdict.decision is not Decision.ALLOW:
        raise HTTPException(status_code=422, detail={"decision": verdict.decision.value, "rules": verdict.rule_ids})
    raw_answer = call_model(CANARY.embed(SYSTEM_PROMPT), request.message)
    checked = output_guard.check(raw_answer)
    if checked.blocked:
        raise HTTPException(
            status_code=502, detail={"decision": "block", "rules": [f.rule_id for f in checked.findings]}
        )
    return ChatResponse(answer=checked.sanitized_text, decision=checked.decision.value)
