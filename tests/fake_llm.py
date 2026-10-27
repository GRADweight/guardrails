"""Lokaler Fake-Server für eine OpenAI-kompatible Chat-API (nur 127.0.0.1, für Tests)."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


@dataclass
class Reply:
    status: int = 200
    body: bytes = b""
    hang: bool = False
    headers: dict[str, str] = field(default_factory=dict)


def chat_reply(content: str) -> Reply:
    body = {"choices": [{"index": 0, "message": {"role": "assistant", "content": content}}]}
    return Reply(200, json.dumps(body).encode())


def verdict_reply(verdict: str, category: str, confidence: float, reason: str = "ok") -> Reply:
    payload = {"verdict": verdict, "category": category, "confidence": confidence, "reason": reason}
    return chat_reply(json.dumps(payload))


@dataclass
class FakeServer:
    url: str
    replies: list[Reply]
    requests: list[dict[str, Any]]
    release: threading.Event


@contextmanager
def fake_llm(replies: list[Reply]) -> Iterator[FakeServer]:
    """Startet einen Server, der die Antworten der Reihe nach liefert (die letzte wiederholt)."""
    queue = list(replies)
    requests: list[dict[str, Any]] = []
    release = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            requests.append({"path": self.path, "headers": dict(self.headers), "body": body})
            reply = queue.pop(0) if len(queue) > 1 else queue[0]
            if reply.hang:
                release.wait(5)
                return
            self.send_response(reply.status)
            for key, value in reply.headers.items():
                self.send_header(key, value)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(reply.body)))
            self.end_headers()
            self.wfile.write(reply.body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[0], server.server_address[1]
        yield FakeServer(f"http://{host!s}:{port}/v1", queue, requests, release)
    finally:
        release.set()
        server.shutdown()
        server.server_close()
