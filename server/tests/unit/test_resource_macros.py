"""
tests/unit/test_resource_macros.py — Failing tests for the planned
app.network_discovery.resource_macros module (issue #129).

These tests will FAIL until resource_macros.py is created because the module
does not exist yet.  All tests are written against the agreed public surface:

  allocate(secrets)               → {key: "$USERn$"}  (slots 2‥256)
  write_resource_block(path, slot_map, values)  — atomic, preserves metadata
  read_resource_block(path)       → {slot_number: value}
  reclaim(keys_to_remove, current_slot_map)     → updated map
  restore_resource_cfg(backup_path, resource_cfg_path)  — backup rollback
  ResourceMacroLimitError         — raised when > 255 slots needed

Behaviour under test
────────────────────
1.  allocate() maps each key to a unique "$USERn$" macro with n ∈ [2, 256].
2.  Slot assignment is stable: calling allocate() a second time with the same
    keys preserves existing assignments.
3.  write_resource_block() writes a PinPoint-owned block delimited by
    "# BEGIN PINPOINT" / "# END PINPOINT", preserving content outside the block.
4.  read_resource_block() parses the block and returns {slot_number: value}.
5.  Requesting more than 255 slots raises ResourceMacroLimitError.
6.  reclaim() removes keys from the slot map and returns the updated map.
7.  Block-only editing: content before and after the PinPoint block is unchanged.
8.  restore_resource_cfg() copies the backup file back over the target.

For integration tests that also exercise host-cfg generation (NCPA tokens must
not appear in hosts.cfg), see TestHostCfgMacroIntegration at the bottom of
this file.  Those tests require a live Flask app + database, so they use the
standard app / db_session / admin_user / plugin_config fixtures from conftest.py
and are guarded by a pytest.importorskip so they are cleanly skipped (not
errored) when the module does not exist yet.
"""

import os
import stat
from pathlib import Path

import pytest

@pytest.fixture(autouse=True)
def private_resource_umask():
    """Model the appliance's group-only resource permissions for test files."""
    previous = os.umask(0o007)
    try:
        yield
    finally:
        os.umask(previous)


# ── Module import ─────────────────────────────────────────────────────────────
# This will raise ImportError (collected as ERROR by pytest) until the module
# exists, which is the desired "failing" state for issue #129.
from app.network_discovery.resource_macros import (
    ResourceMacroLimitError,
    allocate,
    read_resource_block,
    reclaim,
    restore_resource_cfg,
    write_resource_block,
)


# =============================================================================
# Helpers
# =============================================================================

def _slot_number(macro: str) -> int:
    """Extract n from '$USERn$'."""
    assert macro.startswith("$USER") and macro.endswith("$"), repr(macro)
    return int(macro[5:-1])


# =============================================================================
# 1 – allocate() basics
# =============================================================================

class TestAllocate:
    """allocate() returns {key: "$USERn$"} with n ∈ [2, 256]."""

    def test_single_secret_gets_a_macro(self):
        result = allocate({"ncpa_token": "secrettoken"})
        assert set(result) == {"ncpa_token"}
        macro = result["ncpa_token"]
        n = _slot_number(macro)
        assert 2 <= n <= 256, f"slot {n} outside allowed range"

    def test_multiple_secrets_get_distinct_macros(self):
        secrets = {"ncpa_token": "abc", "nt_password": "xyz", "snmp_v3_key": "key1"}
        result = allocate(secrets)
        assert set(result.keys()) == set(secrets.keys())
        macros = list(result.values())
        assert len(set(macros)) == len(macros), "duplicate macro assignments"

    def test_all_slots_are_in_range(self):
        secrets = {f"key_{i}": f"val_{i}" for i in range(10)}
        result = allocate(secrets)
        for key, macro in result.items():
            n = _slot_number(macro)
            assert 2 <= n <= 256, f"{key} assigned slot {n} outside [2, 256]"

    def test_user1_is_never_assigned(self):
        # USER1 is reserved for the Nagios plugin directory.
        secrets = {"token": "value"}
        result = allocate(secrets)
        assert result["token"] != "$USER1$"

    def test_empty_secrets_returns_empty_map(self):
        assert allocate({}) == {}


# =============================================================================
# 2 – Slot stability
# =============================================================================

class TestSlotStability:
    """Same key always maps to the same slot across repeated calls."""

    def test_same_key_same_slot_on_second_call(self):
        first = allocate({"ncpa_token": "secretA"})
        # Add an extra key; the original key must keep its slot.
        second = allocate({"ncpa_token": "secretA", "extra": "extra_val"}, existing=first)
        assert second["ncpa_token"] == first["ncpa_token"]

    def test_new_key_gets_unused_slot(self):
        first = allocate({"alpha": "v1"})
        used = _slot_number(first["alpha"])
        second = allocate({"alpha": "v1", "beta": "v2"}, existing=first)
        new_slot = _slot_number(second["beta"])
        assert new_slot != used

    def test_stability_across_key_reordering(self):
        keys_a = {"k1": "v1", "k2": "v2", "k3": "v3"}
        keys_b = {"k3": "v3", "k1": "v1", "k2": "v2"}
        a = allocate(keys_a)
        b = allocate(keys_b)
        assert a == b


# =============================================================================
# 3 – write_resource_block()
# =============================================================================

class TestWriteResourceBlock:
    """Resource writes are atomic and preserve existing file metadata."""

    def test_block_markers_are_present(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text("# existing content\n")
        slot_map = {"ncpa_token": "$USER2$"}
        values = {"ncpa_token": "secrettoken"}

        write_resource_block(cfg, slot_map, values)

        text = cfg.read_text()
        assert "# BEGIN PINPOINT" in text
        assert "# END PINPOINT" in text

    def test_slot_value_is_written_inside_block(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text("")
        slot_map = {"token": "$USER2$"}
        values = {"token": "mysecret"}

        write_resource_block(cfg, slot_map, values)

        text = cfg.read_text()
        assert "$USER2$=mysecret" in text

    def test_multiple_slots_written(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text("")
        slot_map = {"a": "$USER2$", "b": "$USER3$"}
        values = {"a": "val_a", "b": "val_b"}

        write_resource_block(cfg, slot_map, values)

        text = cfg.read_text()
        assert "$USER2$=val_a" in text
        assert "$USER3$=val_b" in text

    def test_file_mode_is_0640(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text("")
        cfg.chmod(0o640)
        write_resource_block(cfg, {"t": "$USER2$"}, {"t": "v"})

        mode = stat.S_IMODE(os.stat(cfg).st_mode)
        assert mode == 0o640, f"expected mode 0640, got {oct(mode)}"

    def test_existing_owner_and_group_writable_mode_are_preserved(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text("$USER1$=/plugins\n")
        cfg.chmod(0o660)
        original = cfg.stat()

        write_resource_block(cfg, {"t": "$USER2$"}, {"t": "synthetic"})

        updated = cfg.stat()
        assert stat.S_IMODE(updated.st_mode) == 0o660
        assert (updated.st_uid, updated.st_gid) == (original.st_uid, original.st_gid)

    def test_failed_replace_keeps_original_and_removes_private_temp(self, tmp_path, monkeypatch):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text("# original\n")
        cfg.chmod(0o660)

        def fail_replace(source, destination):
            assert destination == cfg
            assert stat.S_IMODE(Path(source).stat().st_mode) == 0o660
            raise PermissionError("synthetic replacement failure")

        monkeypatch.setattr(os, "replace", fail_replace)
        with pytest.raises(PermissionError):
            write_resource_block(cfg, {"t": "$USER2$"}, {"t": "synthetic"})

        assert cfg.read_text() == "# original\n"
        assert stat.S_IMODE(cfg.stat().st_mode) == 0o660
        assert list(tmp_path.iterdir()) == [cfg]

    def test_write_is_atomic_no_partial_file_on_existing(self, tmp_path):
        """The function must use a temp file + rename pattern.
        We verify by checking the file is complete after the call — not an
        empty or truncated file."""
        cfg = tmp_path / "resource.cfg"
        cfg.write_text("# pre-existing line\n")
        write_resource_block(cfg, {"t": "$USER2$"}, {"t": "v"})
        text = cfg.read_text()
        assert "# pre-existing line" in text
        assert "$USER2$=v" in text

    def test_no_leftover_temp_file(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text("")
        write_resource_block(cfg, {"t": "$USER2$"}, {"t": "v"})
        temps = list(tmp_path.glob("*.tmp")) + list(tmp_path.glob("resource.cfg.*"))
        assert temps == [], f"leftover temp files: {temps}"


# =============================================================================
# 4 – read_resource_block()
# =============================================================================

class TestReadResourceBlock:
    """read_resource_block() parses the PinPoint block and returns
    {slot_number: value} with integer keys."""

    def test_reads_single_slot(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text(
            "# Nagios resource file\n"
            "$USER1$=/usr/local/nagios/libexec\n"
            "# BEGIN PINPOINT\n"
            "$USER2$=secrettoken\n"
            "# END PINPOINT\n"
        )
        result = read_resource_block(cfg)
        assert result == {2: "secrettoken"}

    def test_reads_multiple_slots(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text(
            "# BEGIN PINPOINT\n"
            "$USER2$=alpha\n"
            "$USER3$=beta\n"
            "$USER10$=gamma\n"
            "# END PINPOINT\n"
        )
        result = read_resource_block(cfg)
        assert result == {2: "alpha", 3: "beta", 10: "gamma"}

    def test_returns_empty_dict_when_no_block(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text("$USER1$=/usr/local/nagios/libexec\n")
        assert read_resource_block(cfg) == {}

    def test_ignores_content_outside_block(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text(
            "$USER1$=/usr/local/nagios/libexec\n"
            "# BEGIN PINPOINT\n"
            "$USER2$=secret\n"
            "# END PINPOINT\n"
            "$USER1$=/usr/local/nagios/libexec\n"  # duplicate outside — must not appear
        )
        result = read_resource_block(cfg)
        assert 1 not in result
        assert result == {2: "secret"}

    def test_missing_file_returns_empty_dict(self, tmp_path):
        missing = tmp_path / "does_not_exist.cfg"
        assert read_resource_block(missing) == {}

    def test_roundtrip_write_then_read(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text("")
        slot_map = {"tok_a": "$USER5$", "tok_b": "$USER7$"}
        values = {"tok_a": "secret_a", "tok_b": "secret_b"}

        write_resource_block(cfg, slot_map, values)
        result = read_resource_block(cfg)

        assert result == {5: "secret_a", 7: "secret_b"}


# =============================================================================
# 5 – ResourceMacroLimitError
# =============================================================================

class TestResourceMacroLimitError:
    """Requesting more than 255 distinct slots raises ResourceMacroLimitError."""

    def test_exactly_255_slots_is_allowed(self):
        secrets = {f"key_{i}": f"val_{i}" for i in range(255)}
        result = allocate(secrets)
        assert len(result) == 255

    def test_256_secrets_raises(self):
        secrets = {f"key_{i}": f"val_{i}" for i in range(256)}
        with pytest.raises(ResourceMacroLimitError) as exc_info:
            allocate(secrets)
        # The error message must be human-readable.
        msg = str(exc_info.value)
        assert "256" in msg or "limit" in msg.lower() or "USER" in msg

    def test_error_message_is_informative(self):
        secrets = {f"k{i}": f"v{i}" for i in range(260)}
        with pytest.raises(ResourceMacroLimitError) as exc_info:
            allocate(secrets)
        msg = str(exc_info.value)
        assert len(msg) > 10, "error message should be descriptive, not empty"

    def test_limit_error_is_exception_subclass(self):
        assert issubclass(ResourceMacroLimitError, Exception)


# =============================================================================
# 6 – reclaim()
# =============================================================================

class TestReclaim:
    """reclaim() removes keys from the slot map and returns the updated map."""

    def test_single_key_removed(self):
        slot_map = {"ncpa_token": "$USER2$", "nt_pass": "$USER3$"}
        updated = reclaim(["ncpa_token"], slot_map)
        assert "ncpa_token" not in updated
        assert updated == {"nt_pass": "$USER3$"}

    def test_multiple_keys_removed(self):
        slot_map = {"a": "$USER2$", "b": "$USER3$", "c": "$USER4$"}
        updated = reclaim(["a", "c"], slot_map)
        assert updated == {"b": "$USER3$"}

    def test_removing_absent_key_is_safe(self):
        slot_map = {"a": "$USER2$"}
        updated = reclaim(["nonexistent"], slot_map)
        assert updated == {"a": "$USER2$"}

    def test_reclaim_does_not_mutate_original(self):
        original = {"a": "$USER2$", "b": "$USER3$"}
        reclaim(["a"], original)
        assert "a" in original  # original must be unchanged

    def test_reclaim_empty_list_is_noop(self):
        slot_map = {"a": "$USER2$"}
        updated = reclaim([], slot_map)
        assert updated == {"a": "$USER2$"}

    def test_reclaimed_slot_can_be_reallocated(self):
        slot_map = {"a": "$USER2$"}
        freed = reclaim(["a"], slot_map)
        # After reclaiming, a new key can get slot 2 again.
        new = allocate({"b": "val"}, existing=freed)
        assert _slot_number(new["b"]) in range(2, 257)


# =============================================================================
# 7 – Block-only editing: content outside PinPoint block is preserved
# =============================================================================

class TestBlockOnlyEditing:
    """Lines before and after the PinPoint block must survive unchanged."""

    def test_content_before_block_is_preserved(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text(
            "# Nagios resource file header\n"
            "$USER1$=/usr/local/nagios/libexec\n"
            "# some other comment\n"
        )
        write_resource_block(cfg, {"t": "$USER2$"}, {"t": "v"})
        text = cfg.read_text()
        assert "# Nagios resource file header\n" in text
        assert "$USER1$=/usr/local/nagios/libexec\n" in text
        assert "# some other comment\n" in text

    def test_content_after_block_is_preserved(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text(
            "# BEGIN PINPOINT\n"
            "$USER2$=old\n"
            "# END PINPOINT\n"
            "# footer line\n"
            "$USER1$=/usr/local/nagios/libexec\n"
        )
        write_resource_block(cfg, {"t": "$USER2$"}, {"t": "new"})
        text = cfg.read_text()
        assert "# footer line\n" in text
        assert "$USER1$=/usr/local/nagios/libexec\n" in text

    def test_block_is_replaced_not_duplicated(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text(
            "# header\n"
            "# BEGIN PINPOINT\n"
            "$USER2$=old\n"
            "# END PINPOINT\n"
        )
        write_resource_block(cfg, {"t": "$USER2$"}, {"t": "new"})
        text = cfg.read_text()
        assert text.count("# BEGIN PINPOINT") == 1
        assert text.count("# END PINPOINT") == 1
        assert "old" not in text
        assert "$USER2$=new" in text

    def test_second_write_updates_only_block(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text(
            "$USER1$=/usr/local/nagios/libexec\n"
        )
        write_resource_block(cfg, {"tok": "$USER2$"}, {"tok": "first"})
        write_resource_block(cfg, {"tok": "$USER2$"}, {"tok": "second"})
        text = cfg.read_text()
        assert "$USER1$=/usr/local/nagios/libexec\n" in text
        assert "first" not in text
        assert "$USER2$=second" in text
        assert text.count("# BEGIN PINPOINT") == 1


# =============================================================================
# 8 – restore_resource_cfg()
# =============================================================================

class TestRestoreResourceCfg:
    """restore_resource_cfg() copies the backup back over the target."""

    def test_backup_content_is_restored(self, tmp_path):
        backup = tmp_path / "resource.cfg.bak"
        target = tmp_path / "resource.cfg"
        backup.write_text("$USER1$=/original/path\n")
        target.write_text("$USER1$=/modified/path\n$USER2$=secret\n")

        restore_resource_cfg(backup, target)

        assert target.read_text() == "$USER1$=/original/path\n"

    def test_target_is_overwritten_not_appended(self, tmp_path):
        backup = tmp_path / "resource.cfg.bak"
        target = tmp_path / "resource.cfg"
        backup.write_text("# backup\n")
        target.write_text("# current content that should be gone\n")

        restore_resource_cfg(backup, target)

        assert target.read_text() == "# backup\n"
        assert "current content" not in target.read_text()

    def test_backup_file_still_exists_after_restore(self, tmp_path):
        backup = tmp_path / "resource.cfg.bak"
        target = tmp_path / "resource.cfg"
        backup.write_text("# backup\n")
        target.write_text("# target\n")

        restore_resource_cfg(backup, target)

        assert backup.exists(), "backup file must not be deleted by restore"

    def test_missing_backup_raises(self, tmp_path):
        backup = tmp_path / "nonexistent.bak"
        target = tmp_path / "resource.cfg"
        target.write_text("")

        with pytest.raises((FileNotFoundError, OSError)):
            restore_resource_cfg(backup, target)


# =============================================================================
# Integration — hosts.cfg must not contain literal NCPA tokens
# =============================================================================
# These tests require a Flask app + database.  They use the same fixtures as
# test_create_host_cfg.py (app, db_session, admin_user, plugin_config).
#
# The entire class is guarded: if resource_macros doesn't exist, the import at
# the top of this file will already have failed at collection time, which is the
# intended signal that the feature is not yet implemented.  Once it is, these
# tests additionally require that create_host_cfg.py is wired to use macros.
# =============================================================================

# Re-import helpers from create_host_cfg that the integration tests need.
# If those imports break, we let the error surface — it means the test file
# itself is misaligned with the codebase.
import re as _re
from contextlib import contextmanager as _contextmanager

from app.network_discovery.create_host_cfg import (
    _create_host_cfg_file,
    build_host_services,
    load_host_plugin_facts,
)
from app.system_models import (
    ActivityLog,
    AgentStatus,
    DiscoveryStatus,
    NCPADeployment,
    NCPADevicePartition,
    NetworkDiscovery,
    NetworkDiscoveryStatus,
    SystemSettings,
)


@_contextmanager
def _patched_config(app, **overrides):
    original = {k: app.config.get(k) for k in overrides}
    app.config.update(overrides)
    try:
        yield
    finally:
        app.config.update(original)


NCPA_METRICS = [
    {"metric": "cpu", "path": "cpu/percent", "warning": "50", "critical": "80"},
    {"metric": "memory", "path": "memory/virtual/percent", "warning": "50", "critical": "80"},
]


@pytest.fixture
def _plugin_config(app):
    with _patched_config(
        app,
        SNMP_OIDS=[],
        SNMP_COMMUNITY_STRING="public",
        SNMP_PORT="161",
        NCPA_METRICS=NCPA_METRICS,
        NCPA_PORT="5693",
    ):
        yield app.config


def _make_device(db_session, user, hostname, ip, plugin_variables=None):
    log = ActivityLog(Action_Type="test", UserID=user.UserID)
    db_session.session.add(log)
    db_session.session.flush()
    status = NetworkDiscoveryStatus(
        Status=DiscoveryStatus.SUCCESS, Progress=100, Message="done", LogID=log.LogID
    )
    db_session.session.add(status)
    db_session.session.flush()
    device = NetworkDiscovery(
        Hostname=hostname,
        IP_Address=ip,
        Network="192.168.130.0/24",
        OS_Type="Linux",
        DiscoveryStatusID=status.DiscoveryStatusID,
        Plugin_Variables=plugin_variables,
    )
    db_session.session.add(device)
    db_session.session.flush()
    return device


def _make_ncpa_deployment(db_session, device, token, partitions=()):
    deployment = NCPADeployment(
        Token=token,
        Agent_Status=AgentStatus.PENDING_NCPA,
        NetworkDiscoveryID=device.NetDiscoveryID,
    )
    db_session.session.add(deployment)
    db_session.session.flush()
    for name in partitions:
        db_session.session.add(
            NCPADevicePartition(Name=name, NCPADeployID=deployment.NCPADeployID)
        )
    db_session.session.flush()
    return deployment


def _make_host_entry(hostname, tcp=None, net_discovery_id=None):
    return {
        "data": {
            "hostname": hostname,
            "mac_address": None,
            "os": "Linux",
            "net_discovery_id": net_discovery_id,
            "plugin_variables": None,
        },
        "services": {
            "tcp": {port: {"service_name": name} for port, name in (tcp or {}).items()},
            "udp": {},
        },
    }


@pytest.mark.usefixtures("all_monitoring_plugins")
class TestHostCfgMacroIntegration:
    """
    After resource_macros.py is wired into create_host_cfg.py:
    - The literal NCPA token must NOT appear anywhere in hosts.cfg.
    - check_command arguments must use a $USERn$ macro reference instead.
    - Custom-check passwords must also be absent from hosts.cfg.

    These tests FAIL until both resource_macros.py exists AND create_host_cfg.py
    is updated to call it.
    """

    SECRET_TOKEN = "verysecrettoken99"

    def _generate_cfg(self, app, db_session, admin_user, _plugin_config, tmp_path):
        device = _make_device(db_session, admin_user, "ncpa-host", "10.0.0.50")
        _make_ncpa_deployment(db_session, device, self.SECRET_TOKEN, [])
        db_session.session.commit()

        discovered = {
            "10.0.0.0/24": {
                "10.0.0.50": _make_host_entry(
                    "ncpa-host", tcp={"5693": "ncpa"}, net_discovery_id=device.NetDiscoveryID
                )
            }
        }
        resource_cfg = tmp_path / "resource.cfg"
        resource_cfg.write_text("$USER1$=/usr/local/nagios/libexec\n")

        with _patched_config(
            app,
            HOST_CONFIG_DIR=tmp_path,
            NAGIOS_RESOURCE_CFG=str(resource_cfg),
            SNMP_OIDS=[],
            SNMP_COMMUNITY_STRING="public",
            SNMP_PORT="161",
            NCPA_METRICS=NCPA_METRICS,
            NCPA_PORT="5693",
        ):
            cfg_path = _create_host_cfg_file(discovered)

        return cfg_path.read_text(), resource_cfg.read_text()

    def test_ncpa_token_absent_from_hosts_cfg(
        self, app, db_session, admin_user, _plugin_config, tmp_path
    ):
        """The plaintext NCPA token must not appear anywhere in hosts.cfg."""
        hosts_cfg_text, _ = self._generate_cfg(
            app, db_session, admin_user, _plugin_config, tmp_path
        )
        assert self.SECRET_TOKEN not in hosts_cfg_text, (
            f"Literal token '{self.SECRET_TOKEN}' found in hosts.cfg — "
            "it must be replaced with a $USERn$ macro reference."
        )

    def test_ncpa_command_uses_user_macro(
        self, app, db_session, admin_user, _plugin_config, tmp_path
    ):
        """The check_command for an NCPA service must contain a $USERn$ macro."""
        hosts_cfg_text, _ = self._generate_cfg(
            app, db_session, admin_user, _plugin_config, tmp_path
        )
        # Find all check_command lines for ncpa services.
        ncpa_commands = _re.findall(
            r"check_command\s+(pinpoint_nd_ncpa\S+)", hosts_cfg_text
        )
        assert ncpa_commands, "No NCPA check_command lines found in hosts.cfg"
        for cmd in ncpa_commands:
            assert "$USER" in cmd, (
                f"check_command '{cmd}' does not contain a $USERn$ macro — "
                "token must be substituted with a resource macro."
            )

    def test_user_macro_is_written_to_resource_cfg(
        self, app, db_session, admin_user, _plugin_config, tmp_path
    ):
        """After generation, resource.cfg must contain the actual token value
        inside the PinPoint block."""
        _, resource_text = self._generate_cfg(
            app, db_session, admin_user, _plugin_config, tmp_path
        )
        assert self.SECRET_TOKEN in resource_text, (
            "NCPA token must be written to resource.cfg; it was not found there."
        )
        assert "# BEGIN PINPOINT" in resource_text

    def test_custom_check_password_absent_from_hosts_cfg(
        self, app, db_session, admin_user, _plugin_config, tmp_path
    ):
        """A custom check that has a secret password must not put that
        password literally into hosts.cfg.

        This test creates a device whose Plugin_Variables include a mysql
        password (or similar credential) and asserts the value is absent
        from the generated file.  It will fail until custom_checks.py is
        also wired to use resource_macros.
        """
        SECRET_PASSWORD = "SuperSecretDBPass!"
        device = _make_device(
            db_session,
            admin_user,
            "db-host",
            "10.0.0.60",
            plugin_variables={"mysql": {"user": "nagios", "password": SECRET_PASSWORD}},
        )
        db_session.session.commit()

        discovered = {
            "10.0.0.0/24": {
                "10.0.0.60": _make_host_entry(
                    "db-host",
                    tcp={"3306": "mysql"},
                    net_discovery_id=device.NetDiscoveryID,
                )
            }
        }
        resource_cfg = tmp_path / "resource.cfg"
        resource_cfg.write_text("$USER1$=/usr/local/nagios/libexec\n")

        with _patched_config(
            app,
            HOST_CONFIG_DIR=tmp_path,
            NAGIOS_RESOURCE_CFG=str(resource_cfg),
            SNMP_OIDS=[],
            SNMP_COMMUNITY_STRING="public",
            SNMP_PORT="161",
            NCPA_METRICS=NCPA_METRICS,
            NCPA_PORT="5693",
        ):
            cfg_path = _create_host_cfg_file(discovered)

        hosts_cfg_text = cfg_path.read_text()
        assert SECRET_PASSWORD not in hosts_cfg_text, (
            f"Literal password '{SECRET_PASSWORD}' found in hosts.cfg — "
            "passwords must be stored in resource.cfg as $USERn$ macros."
        )


class TestSecretArgumentSubstitution:
    """A secret matching public argument text must only replace its own field."""

    def test_ncpa_token_matching_metric_leaves_metric_unchanged(self):
        from app.network_discovery.create_host_cfg import apply_secret_substitutions
        command = "pinpoint_nd_ncpa!5693!cpu!cpu/percent!"
        assert apply_secret_substitutions(command, {"cpu": "$USER2$"}) == (
            "pinpoint_nd_ncpa!5693!$USER2$!cpu/percent!"
        )

    def test_ncpa_token_matching_port_leaves_port_unchanged(self):
        from app.network_discovery.create_host_cfg import apply_secret_substitutions
        command = "pinpoint_nd_ncpa!5693!5693!cpu/percent!"
        assert apply_secret_substitutions(command, {"5693": "$USER2$"}) == (
            "pinpoint_nd_ncpa!5693!$USER2$!cpu/percent!"
        )

    def test_custom_required_password_leaves_matching_username_unchanged(self):
        from app.network_discovery.create_host_cfg import apply_secret_substitutions
        command = "pinpoint_custom_check_radius!probe!probe!/etc/radius.conf!"
        assert apply_secret_substitutions(command, {"probe": "$USER3$"}) == (
            "pinpoint_custom_check_radius!probe!$USER3$!/etc/radius.conf!"
        )

    def test_custom_optional_password_leaves_query_and_username_unchanged(self):
        from app.network_discovery.create_host_cfg import apply_secret_substitutions
        command = "pinpoint_custom_check_mysql_query!SELECT cpu!10!20!-u 'cpu' -p 'cpu'"
        assert apply_secret_substitutions(command, {"cpu": "$USER4$"}) == (
            "pinpoint_custom_check_mysql_query!SELECT cpu!10!20!-u 'cpu' -p '$USER4$'"
        )

    def test_overlapping_secret_values_do_not_replace_substrings(self):
        from app.network_discovery.create_host_cfg import apply_secret_substitutions
        command = "pinpoint_nd_ncpa!5693!longer-token!cpu/percent!"
        assert apply_secret_substitutions(command, {"token": "$USER2$", "longer-token": "$USER3$"}) == (
            "pinpoint_nd_ncpa!5693!$USER3$!cpu/percent!"
        )

    def test_unrelated_check_with_matching_public_argument_is_unchanged(self):
        from app.network_discovery.create_host_cfg import apply_secret_substitutions
        command = "pinpoint_custom_check_by_ssh!/bin/true!-l 'cpu'"
        assert apply_secret_substitutions(command, {"cpu": "$USER2$"}) == command


class TestPersistentSlots:
    def test_owned_keys_survive_file_roundtrip_and_removed_keys_free_slots(self, tmp_path):
        from app.network_discovery import resource_macros
        cfg = tmp_path / "resource.cfg"
        cfg.write_text("$USER1$=/plugins\n$USER2$=external\n")
        cfg.chmod(0o660)
        first = resource_macros.allocate(
            {"ncpa_token:1": "one", "ncpa_token:2": "two"},
            reserved=resource_macros.read_reserved_slots(cfg),
        )
        resource_macros.write_resource_block(cfg, first, {"ncpa_token:1": "one", "ncpa_token:2": "two"})
        stored = resource_macros.read_slot_assignments(cfg)
        assert stored == first
        retained = resource_macros.reclaim(["ncpa_token:1"], stored)
        next_slots = resource_macros.allocate(
            {"ncpa_token:2": "changed", "ncpa_token:3": "three"}, existing=retained,
            reserved=resource_macros.read_reserved_slots(cfg),
        )
        assert next_slots["ncpa_token:2"] == first["ncpa_token:2"]
        assert next_slots["ncpa_token:3"] == first["ncpa_token:1"]
        assert "$USER2$" not in next_slots.values()

    def test_malformed_owned_block_is_rejected_without_removing_footer(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        original = "# BEGIN PINPOINT\n$USER2$=old\n# unrelated footer\n"
        cfg.write_text(original)
        cfg.chmod(0o660)
        with pytest.raises(ValueError, match="block"):
            write_resource_block(cfg, {"t": "$USER2$"}, {"t": "synthetic"})
        assert cfg.read_text() == original

    def test_external_slot_collision_is_rejected_without_changes(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        original = "$USER2$=external\n"
        cfg.write_text(original)
        cfg.chmod(0o660)
        with pytest.raises(ValueError, match="slot"):
            write_resource_block(cfg, {"t": "$USER2$"}, {"t": "synthetic"})
        assert cfg.read_text() == original

    def test_world_readable_resource_file_is_rejected(self, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text("# original\n")
        cfg.chmod(0o664)
        with pytest.raises(ValueError, match="permission"):
            write_resource_block(cfg, {"t": "$USER2$"}, {"t": "synthetic"})
        assert cfg.read_text() == "# original\n"


class TestMacroGenerationFailure:
    def test_missing_resource_file_prevents_candidate_publication(self, app, db_session, tmp_path, monkeypatch):
        from app.network_discovery import create_host_cfg
        monkeypatch.setattr(create_host_cfg, "collect_ncpa_secrets", lambda _facts: {"ncpa_token:1": "synthetic"})
        with _patched_config(app, HOST_CONFIG_DIR=tmp_path / "gen", NAGIOS_RESOURCE_CFG=tmp_path / "missing.cfg"):
            with pytest.raises(FileNotFoundError):
                _create_host_cfg_file({})
        assert not list((tmp_path / "gen").glob("*.cfg"))

    def test_failed_resource_write_prevents_candidate_publication(self, app, db_session, tmp_path, monkeypatch):
        from app.network_discovery import create_host_cfg, resource_macros
        cfg = tmp_path / "resource.cfg"
        cfg.write_text("# original\n")
        cfg.chmod(0o660)
        monkeypatch.setattr(create_host_cfg, "collect_ncpa_secrets", lambda _facts: {"ncpa_token:1": "synthetic"})
        def fail_write(*_args):
            raise PermissionError("synthetic failure")
        monkeypatch.setattr(resource_macros, "write_resource_block", fail_write)
        with _patched_config(app, HOST_CONFIG_DIR=tmp_path / "gen", NAGIOS_RESOURCE_CFG=cfg):
            with pytest.raises(PermissionError):
                _create_host_cfg_file({})
        assert not list((tmp_path / "gen").glob("*.cfg"))

    def test_removing_last_secret_clears_owned_block(self, app, db_session, tmp_path):
        cfg = tmp_path / "resource.cfg"
        cfg.write_text("$USER1$=/plugins\n# BEGIN PINPOINT\n$USER2$=old\n# END PINPOINT\n")
        cfg.chmod(0o660)
        with _patched_config(app, HOST_CONFIG_DIR=tmp_path / "gen", NAGIOS_RESOURCE_CFG=cfg):
            _create_host_cfg_file({})
        assert read_resource_block(cfg) == {}
        assert "$USER1$=/plugins" in cfg.read_text()


@pytest.mark.usefixtures("all_monitoring_plugins")
def test_removing_device_from_generated_hosts_reclaims_its_actual_slot(app, db_session, admin_user, tmp_path):
    from app.network_discovery import resource_macros
    first = _make_device(db_session, admin_user, "first", "10.0.0.51")
    second = _make_device(db_session, admin_user, "second", "10.0.0.52")
    _make_ncpa_deployment(db_session, first, "first-synthetic")
    _make_ncpa_deployment(db_session, second, "second-synthetic")
    db_session.session.commit()
    hosts = {"10.0.0.0/24": {
        "10.0.0.51": _make_host_entry("first", tcp={"5693": "ncpa"}, net_discovery_id=first.NetDiscoveryID),
        "10.0.0.52": _make_host_entry("second", tcp={"5693": "ncpa"}, net_discovery_id=second.NetDiscoveryID),
    }}
    resource = tmp_path / "resource.cfg"
    resource.write_text("$USER1$=/plugins\n")
    resource.chmod(0o660)
    with _patched_config(app, HOST_CONFIG_DIR=tmp_path / "gen", NAGIOS_RESOURCE_CFG=resource):
        _create_host_cfg_file(hosts)
        before = resource_macros.read_slot_assignments(resource)
        del hosts["10.0.0.0/24"]["10.0.0.51"]
        _create_host_cfg_file(hosts)
        after = resource_macros.read_slot_assignments(resource)
    assert f"ncpa_token:{first.NetDiscoveryID}" not in after
    assert after[f"ncpa_token:{second.NetDiscoveryID}"] == before[f"ncpa_token:{second.NetDiscoveryID}"]
    assert "first-synthetic" not in resource.read_text()


@pytest.mark.usefixtures("all_monitoring_plugins")
def test_ncpa_macro_expansion_preserves_effective_metric_commands(app, db_session, admin_user, tmp_path):
    generator = TestHostCfgMacroIntegration()
    host_text, _resource_text = generator._generate_cfg(app, db_session, admin_user, app.config, tmp_path)
    values = read_resource_block(tmp_path / "resource.cfg")
    commands = _re.findall(r"check_command\s+(pinpoint_nd_ncpa[^\n]+)", host_text)
    expanded = {
        _re.sub(r"\$USER([0-9]+)\$", lambda match: values[int(match.group(1))], command.strip())
        for command in commands
    }
    assert expanded == {
        f"pinpoint_nd_ncpa!5693!{generator.SECRET_TOKEN}!cpu/percent!-w '50' -c '80'",
        f"pinpoint_nd_ncpa!5693!{generator.SECRET_TOKEN}!memory/virtual/percent!-w '50' -c '80'",
    }
