"""Gemeinsame Fixtures. Verhindert jeden Netzwerkzugriff ausser auf Loopback-Adressen."""

from __future__ import annotations

import ipaddress
import socket
from typing import Any

import pytest

_original_connect = socket.socket.connect


def _guarded_connect(self: socket.socket, address: Any) -> Any:
    host = address[0] if isinstance(address, tuple) else address
    try:
        is_loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        is_loopback = host == "localhost"
    if not is_loopback:
        raise RuntimeError(f"Netzwerkzugriff in Tests verboten: {address!r}")
    return _original_connect(self, address)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)
