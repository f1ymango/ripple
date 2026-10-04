"""Reader CLI preserves run evidence, including when run IDs collide."""
import json
from datetime import datetime
from pathlib import Path

import pytest

from src.reader import run, sample


@pytest.fixture
def cli(tmp_path, monkeypatch):
    fixture = Path(__file__).parent / "fixtures" / "stn_snapshot_20260915-0000.xml"
    stn = sample.parse_messages(fixture.read_bytes())[0]
    messages = tmp_path / "messages.jsonl"
    messages.write_text(json.dumps({"stn": stn}) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["run", "--messages", str(messages)])
    calls = []
    monkeypatch.setattr(run.reader, "read_message",
                        lambda *args, **kwargs: calls.append(args) or {"test": "mock reply"})
    return messages, calls


def test_colliding_run_id_preserves_previous_result(cli, tmp_path, monkeypatch):
    class FrozenTime:
        @staticmethod
        def now(tz):
            return datetime(2026, 10, 1, 12, 0, tzinfo=tz)

    monkeypatch.setattr(run, "datetime", FrozenTime)
    run.main()
    [result] = (tmp_path / "results" / "reader").glob("*.jsonl")
    saved = result.read_bytes()
    with pytest.raises(FileExistsError):
        run.main()
    assert result.read_bytes() == saved
    assert len(cli[1]) == 1  # Collision fails before another model call.


def test_empty_input_creates_no_result(cli, tmp_path):
    cli[0].write_text("\n \n", encoding="utf-8")
    with pytest.raises(SystemExit):
        run.main()
    assert not (tmp_path / "results").exists()
    assert not cli[1]


def test_blank_lines_are_ignored(cli, tmp_path):
    messages, calls = cli
    messages.write_text("\n" + messages.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    run.main()
    [result] = (tmp_path / "results" / "reader").glob("*.jsonl")
    assert len(result.read_text(encoding="utf-8").splitlines()) == len(calls) == 1
