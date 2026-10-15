"""Tests for server/scripts/pinpoint_event_handler.py, the program Nagios runs on a state change.

It must write one small validated JSON file per event and nothing else; every hostile or
malformed argument must be refused with nothing written (threats T3, T7 in the design).
"""
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "pinpoint_event_handler.py"
spec = importlib.util.spec_from_file_location("pinpoint_event_handler", SCRIPT)
handler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handler)

SERVICE_ARGS = ["service", "CRITICAL", "HARD", "3", "web-01", "HTTP", "1760432100"]
HOST_ARGS = ["host", "DOWN", "HARD", "3", "web-01", "1760432100"]

HOSTILE = [
    "a;b", "a$(id)", "a`id`", "a'b", 'a"b', "a\nb", "a\rb", "a\x00b", "a|b", "a&b", "a>b", "a<b",
    "a\\b", "a{b}", "a*b", "../../etc/passwd", "ünï", "a\tb", "",
]


@pytest.fixture()
def spool(tmp_path):
    return tmp_path


def files(spool):
    return sorted(p.name for p in spool.iterdir())


# ==========================================================
# VALID EVENTS
# ==========================================================

def test_service_event_is_written_as_one_json_file(spool):
    assert handler.main(SERVICE_ARGS, spool_dir=str(spool)) == 0
    (name,) = files(spool)
    assert re.fullmatch(r"\d{10,}-\d+\.json", name)
    assert json.loads((spool / name).read_text()) == {
        "v": 1, "kind": "service", "host": "web-01", "service": "HTTP", "state": "CRITICAL",
        "state_type": "HARD", "attempt": 3, "last_change": 1760432100,
    }


def test_host_event_has_no_service(spool):
    assert handler.main(HOST_ARGS, spool_dir=str(spool)) == 0
    (name,) = files(spool)
    body = json.loads((spool / name).read_text())
    assert body["kind"] == "host" and body["service"] is None and body["state"] == "DOWN"


def test_service_names_with_spaces_and_slashes_are_accepted(spool):
    args = ["service", "WARNING", "SOFT", "1", "db_01.lan", "Port 5432/tcp: postgres", "1760432100"]
    assert handler.main(args, spool_dir=str(spool)) == 0


def test_the_content_is_one_line(spool):
    handler.main(SERVICE_ARGS, spool_dir=str(spool))
    (name,) = files(spool)
    assert (spool / name).read_text().count("\n") <= 1


def test_two_events_make_two_files(spool):
    handler.main(SERVICE_ARGS, spool_dir=str(spool))
    handler.main(SERVICE_ARGS, spool_dir=str(spool))
    assert len(files(spool)) == 2


def test_no_temporary_file_is_left_behind(spool):
    handler.main(SERVICE_ARGS, spool_dir=str(spool))
    assert not [n for n in files(spool) if n.startswith(".")]


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes")
def test_file_is_group_readable_but_not_world_accessible(spool):
    handler.main(SERVICE_ARGS, spool_dir=str(spool))
    (name,) = files(spool)
    assert (spool / name).stat().st_mode & 0o777 == 0o660


# ==========================================================
# HOSTILE AND MALFORMED INPUT: NOTHING IS WRITTEN
# ==========================================================

@pytest.mark.parametrize("bad", HOSTILE)
def test_hostile_host_name_is_refused(spool, bad):
    args = list(SERVICE_ARGS)
    args[4] = bad
    assert handler.main(args, spool_dir=str(spool)) != 0
    assert files(spool) == []


@pytest.mark.parametrize("bad", [b for b in HOSTILE if b != ""] + ["", "x" * 151])
def test_hostile_service_name_is_refused(spool, bad):
    args = list(SERVICE_ARGS)
    args[5] = bad
    assert handler.main(args, spool_dir=str(spool)) != 0
    assert files(spool) == []


def test_over_long_host_name_is_refused(spool):
    args = list(SERVICE_ARGS)
    args[4] = "h" * 101
    assert handler.main(args, spool_dir=str(spool)) != 0
    assert files(spool) == []


@pytest.mark.parametrize("state", ["critical", "DOWN", "OK; reboot", "", "FLAPPING"])
def test_service_state_must_be_a_service_state(spool, state):
    args = list(SERVICE_ARGS)
    args[1] = state
    assert handler.main(args, spool_dir=str(spool)) != 0
    assert files(spool) == []


@pytest.mark.parametrize("state", ["CRITICAL", "up", "", "DOWN;x"])
def test_host_state_must_be_a_host_state(spool, state):
    args = list(HOST_ARGS)
    args[1] = state
    assert handler.main(args, spool_dir=str(spool)) != 0
    assert files(spool) == []


@pytest.mark.parametrize("state_type", ["hard", "FIRM", "", "HARD;x"])
def test_state_type_must_be_soft_or_hard(spool, state_type):
    args = list(SERVICE_ARGS)
    args[2] = state_type
    assert handler.main(args, spool_dir=str(spool)) != 0
    assert files(spool) == []


@pytest.mark.parametrize("attempt", ["0", "-1", "abc", "1.5", "", "1000", "3;x"])
def test_attempt_must_be_a_small_positive_number(spool, attempt):
    args = list(SERVICE_ARGS)
    args[3] = attempt
    assert handler.main(args, spool_dir=str(spool)) != 0
    assert files(spool) == []


@pytest.mark.parametrize("last_change", ["-1", "abc", "", "1" * 13, "17.5", "1;x"])
def test_last_change_must_be_epoch_seconds(spool, last_change):
    args = list(SERVICE_ARGS)
    args[6] = last_change
    assert handler.main(args, spool_dir=str(spool)) != 0
    assert files(spool) == []


@pytest.mark.parametrize("args", [
    [], ["service"], ["other", "OK", "HARD", "1", "h", "1"], SERVICE_ARGS + ["extra"],
    HOST_ARGS + ["extra"], HOST_ARGS[:-1], SERVICE_ARGS[:-1],
])
def test_wrong_kind_or_argument_count_is_refused(spool, args):
    assert handler.main(args, spool_dir=str(spool)) != 0
    assert files(spool) == []


def test_a_missing_spool_folder_fails_without_creating_it(tmp_path):
    missing = tmp_path / "nope"
    assert handler.main(SERVICE_ARGS, spool_dir=str(missing)) != 0
    assert not missing.exists()


# ==========================================================
# FLOOD CONTROL
# ==========================================================

def test_it_stops_writing_when_the_folder_holds_1000_files(spool):
    for i in range(handler.MAX_SPOOL_FILES):
        (spool / f"{i}-1.json").write_text("{}")
    assert handler.main(SERVICE_ARGS, spool_dir=str(spool)) == 0  # quiet exit, Nagios is not disturbed
    assert len(files(spool)) == handler.MAX_SPOOL_FILES


def test_it_writes_again_once_below_the_limit(spool):
    for i in range(handler.MAX_SPOOL_FILES - 1):
        (spool / f"{i}-1.json").write_text("{}")
    handler.main(SERVICE_ARGS, spool_dir=str(spool))
    assert len(files(spool)) == handler.MAX_SPOOL_FILES


# ==========================================================
# THE PROGRAM DOES NOTHING ELSE
# ==========================================================

def test_the_script_never_opens_a_shell_or_the_network():
    source = SCRIPT.read_text()
    for forbidden in ("subprocess", "os.system", "os.popen", "socket", "urllib", "http.client", "shell=True", "eval(", "exec("):
        assert forbidden not in source, forbidden
