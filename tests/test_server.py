from __future__ import annotations

import json
import threading
import urllib.request

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


def test_health_endpoint_returns_status() -> None:
    server, thread = _start_server()
    try:
        port = server.server_address[1]
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz") as response:
            payload = json.loads(response.read().decode("utf-8"))

        assert payload["status"] == "ok"
        assert payload["service"] == "enterprise-adapters"
        assert payload["environment"] == "test"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


def test_unknown_route_returns_not_found() -> None:
    server, thread = _start_server()
    try:
        port = server.server_address[1]
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/missing")
        except Exception as error:  # noqa: BLE001 - stdlib urllib raises HTTPError
            assert getattr(error, "code", None) == 404
        else:
            raise AssertionError("Expected a 404 response")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)
