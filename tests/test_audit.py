from __future__ import annotations

from pathlib import Path

from enterprise_adapters.audit import InMemoryAuditTrail, SQLiteAuditTrail, build_audit_trail


def test_sqlite_audit_trail_persists_events(tmp_path: Path) -> None:
    trail = SQLiteAuditTrail(tmp_path / "audit.sqlite3")
    trail.record("execution.completed", action_name="create_ticket", approval_id="abc")
    trail.record("policy.evaluated", decision="allow")

    events = trail.events()
    assert len(events) == 2
    assert events[0].event_type == "execution.completed"
    assert events[0].details["action_name"] == "create_ticket"
    assert events[1].event_type == "policy.evaluated"


def test_sqlite_audit_trail_survives_restart(tmp_path: Path) -> None:
    db = tmp_path / "audit.sqlite3"
    SQLiteAuditTrail(db).record("first.event")
    # Simulate restart by opening a new instance pointing at same file
    trail2 = SQLiteAuditTrail(db)
    assert len(trail2.events()) == 1


def test_build_audit_trail_returns_sqlite_when_path_set(tmp_path: Path) -> None:
    trail = build_audit_trail(tmp_path / "audit.sqlite3")
    assert isinstance(trail, SQLiteAuditTrail)


def test_build_audit_trail_returns_in_memory_when_no_path(monkeypatch) -> None:
    monkeypatch.delenv("AUDIT_DB_PATH", raising=False)
    trail = build_audit_trail()
    assert isinstance(trail, InMemoryAuditTrail)
