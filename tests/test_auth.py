from __future__ import annotations

import json
import os
import threading
import urllib.request

import pytest

from enterprise_adapters.contracts import AdapterContext
from enterprise_adapters.server import AdapterHTTPServer, AdapterRequestHandler


def _start_server() -> tuple[AdapterHTTPServer, threading.Thread]:
    server = AdapterHTTPServer(
        ("127.0.0.1", 0),
        AdapterRequestHandler,
        AdapterContext(adapter_name="enterprise-adapters", environment="test"),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _get(url: str, token: str | None = None) -> tuple[int, dict]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read().decode("utf-8")) if exc.fp else {}
        return exc.code, body


def test_healthz_is_public_no_token_needed() -> None:
    server, thread = _start_server()
    try:
        status, payload = _get(f"http://127.0.0.1:{server.server_address[1]}/healthz")
        assert status == 200
        assert payload["status"] == "ok"
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=1)


def test_root_returns_401_when_auth_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADAPTER_API_KEY", "secret-token-xyz")
    server, thread = _start_server()
    try:
        status, payload = _get(f"http://127.0.0.1:{server.server_address[1]}/")
        assert status == 401
        assert payload["status"] == "unauthorized"
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=1)
        monkeypatch.delenv("ADAPTER_API_KEY", raising=False)


def test_root_returns_200_with_correct_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADAPTER_API_KEY", "secret-token-xyz")
    server, thread = _start_server()
    try:
        status, payload = _get(
            f"http://127.0.0.1:{server.server_address[1]}/",
            token="secret-token-xyz",
        )
        assert status == 200
        assert payload["status"] == "ok"
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=1)
        monkeypatch.delenv("ADAPTER_API_KEY", raising=False)


def test_root_returns_200_when_auth_disabled() -> None:
    # No ADAPTER_API_KEY set — auth is disabled in dev mode
    os.environ.pop("ADAPTER_API_KEY", None)
    server, thread = _start_server()
    try:
        status, payload = _get(f"http://127.0.0.1:{server.server_address[1]}/")
        assert status == 200
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=1)
