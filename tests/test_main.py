from enterprise_adapters.__main__ import main


def test_main_runs(capsys) -> None:
    assert main() == 0
    output = capsys.readouterr().out
    assert "Phase 3 adapter layer initialized" in output
