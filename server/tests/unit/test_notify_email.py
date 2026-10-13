"""Tests for server/scripts/pinpoint_notify_email.py, the HTML notification email builder."""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "pinpoint_notify_email.py"
spec = importlib.util.spec_from_file_location("pinpoint_notify_email", SCRIPT)
notify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notify)

SERVICE_ARGS = [
    "service", "type=PROBLEM", "host=web01", "address=10.77.0.2", "service=HTTP",
    "state=CRITICAL", "output=HTTP CRITICAL - connection refused", "time=Tue Oct 13 14:00:00 UTC 2026",
    "to=admin@example.com",
]
HOST_ARGS = ["host", "type=PROBLEM", "host=db01", "address=10.77.0.3", "state=DOWN",
             "output=CRITICAL - Host Unreachable", "to=admin@example.com"]


def build(args):
    kind, fields = notify.parse(args)
    return notify.build_message(kind, fields)


def test_service_message_has_text_and_html_parts_and_subject():
    msg = build(SERVICE_ARGS)
    assert msg["To"] == "admin@example.com"
    assert msg["Subject"] == "[PinPoint] CRITICAL: web01 / HTTP"
    assert msg.is_multipart()
    assert msg.get_body(("plain",)) is not None
    html_part = msg.get_body(("html",)).get_content()
    assert "CRITICAL" in html_part and "web01" in html_part and "connection refused" in html_part


def test_host_message_has_no_service_row():
    msg = build(HOST_ARGS)
    assert msg["Subject"] == "[PinPoint] DOWN: db01"
    assert "Service" not in msg.get_body(("plain",)).get_content()


def test_recovery_subject():
    args = [a.replace("type=PROBLEM", "type=RECOVERY").replace("state=CRITICAL", "state=OK") for a in SERVICE_ARGS]
    assert build(args)["Subject"] == "[PinPoint] RECOVERY: web01 / HTTP is OK"


def test_html_escapes_untrusted_values():
    args = [a.replace("output=HTTP CRITICAL - connection refused", "output=<script>alert(1)</script>") for a in SERVICE_ARGS]
    body = build(args).get_body(("html",)).get_content()
    assert "<script>" not in body
    assert "&lt;script&gt;" in body


def test_control_characters_cannot_inject_headers():
    args = [a.replace("service=HTTP", "service=HTTP\r\nBcc: attacker@example.com") for a in SERVICE_ARGS]
    msg = build(args)
    assert msg["Bcc"] is None
    assert "\n" not in msg["Subject"] and "\r" not in msg["Subject"]


@pytest.mark.parametrize("bad_to", ["", "not-an-email", "a@b", "x@example.com\nBcc: y@example.com"])
def test_invalid_recipient_is_rejected(bad_to):
    args = [a for a in SERVICE_ARGS if not a.startswith("to=")] + [f"to={bad_to}"]
    with pytest.raises(notify.InputRejected):
        notify.parse(args)


def test_unknown_key_kind_and_missing_service_are_rejected():
    with pytest.raises(notify.InputRejected):
        notify.parse(SERVICE_ARGS + ["bogus=1"])
    with pytest.raises(notify.InputRejected):
        notify.parse(["router"] + SERVICE_ARGS[1:])
    with pytest.raises(notify.InputRejected):
        notify.parse([a for a in SERVICE_ARGS if not a.startswith("service=")])


def test_long_values_are_capped():
    args = [a.replace("output=HTTP CRITICAL - connection refused", "output=" + "x" * 5000) for a in SERVICE_ARGS]
    _, fields = notify.parse(args)
    assert len(fields["output"]) == 1000


def test_unknown_state_still_renders():
    args = [a.replace("state=CRITICAL", "state=SOMETHING") for a in SERVICE_ARGS]
    assert "SOMETHING" in build(args).get_body(("html",)).get_content()


def html_of(args):
    return build(args).get_body(("html",)).get_content()


def test_down_host_headline_pill_and_packet_loss_metric():
    args = HOST_ARGS[:-2] + ["state=DOWN", "output=PING CRITICAL - Packet loss = 100%", "to=admin@example.com"]
    args = [a for a in args if not a.startswith("output=CRITICAL")]
    body = html_of(args)
    assert "db01 is unreachable" in body
    assert "CRITICAL ALERT" in body
    assert "100% Packet Loss" in body
    assert "Check device connectivity and network configuration." in body


def test_packet_loss_is_parsed_or_left_out():
    assert notify.packet_loss("PING CRITICAL - Packet loss = 100%") == "100% Packet Loss"
    assert notify.packet_loss("PING WARNING - Packet loss = 20.50%, RTA = 1ms") == "20.5% Packet Loss"
    assert notify.packet_loss("HTTP CRITICAL - connection refused") is None
    assert "Packet Loss" not in html_of(SERVICE_ARGS)


def test_detected_time_is_converted_to_utc_from_timet():
    args = SERVICE_ARGS + ["timet=1791905860"]
    body = html_of(args)
    assert "Oct 13, 2026 · 15:37:40 UTC" in body
    assert "Detected (UTC)" in body


def test_bad_timet_falls_back_to_the_time_text():
    body = html_of(SERVICE_ARGS + ["timet=notanumber"])
    assert "Tue Oct 13 14:00:00 UTC 2026" in body


@pytest.mark.parametrize("kind_type,state,word,colour", [
    ("PROBLEM", "WARNING", "needs attention", notify.AMBER),
    ("PROBLEM", "CRITICAL", "is critical", notify.RED),
    ("RECOVERY", "OK", "has recovered", notify.GREEN),
    ("ACKNOWLEDGEMENT", "CRITICAL", "was acknowledged", notify.BLUE),
])
def test_wording_and_colour_follow_state_and_type(kind_type, state, word, colour):
    args = [a.replace("type=PROBLEM", f"type={kind_type}").replace("state=CRITICAL", f"state={state}") for a in SERVICE_ARGS]
    body = html_of(args)
    assert word in body
    assert colour in body


def test_recovery_host_headline_is_back_online():
    args = [a.replace("type=PROBLEM", "type=RECOVERY").replace("state=DOWN", "state=UP") for a in HOST_ARGS]
    assert "db01 is back online" in html_of(args)


def test_layout_is_email_safe_and_responsive():
    body = html_of(SERVICE_ARGS)
    assert notify.PAGE in body and notify.CARD in body
    assert "max-width:600px" in body
    assert "@media only screen and (max-width:620px)" in body
    for forbidden in ("<svg", "<img", "gradient(", "<script", "<link"):
        assert forbidden not in body


def test_comment_is_shown_for_custom_notifications():
    args = [a.replace("type=PROBLEM", "type=CUSTOM") for a in SERVICE_ARGS] + ["comment=Automatic recovery failed (run 482)."]
    assert "Automatic recovery failed (run 482)." in html_of(args)


def test_blend_mixes_colours():
    assert notify.blend("#ffffff", "#000000", 0.5) == "#808080"
    assert notify.blend("#ff0000", "#0000ff", 0) == "#0000ff"


def test_print_mode_writes_message_and_does_not_send(capsys):
    assert notify.main(["--print"] + SERVICE_ARGS) == 0
    out = capsys.readouterr().out
    assert "Subject: [PinPoint] CRITICAL: web01 / HTTP" in out
    assert "text/html" in out


def test_main_returns_1_on_bad_input_and_2_on_no_arguments(capsys):
    assert notify.main(["service", "to=nope"]) == 1
    assert notify.main([]) == 2


def test_sendmail_failure_returns_3(monkeypatch):
    def boom(*a, **k):
        raise FileNotFoundError()
    monkeypatch.setattr(notify.subprocess, "run", boom)
    assert notify.main(SERVICE_ARGS) == 3
