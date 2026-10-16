"""
tests/unit/test_snmp_v3.py — SNMP version choice and v3 credentials (issue #127, parts 14.1/14.2):

  * app/network_discovery/plugin_registry.py   the snmp_v3 command and its validation
  * app/network_discovery/device_plugin_variables.py   per-device override validation and secrets
  * app/network_discovery/create_host_cfg.py   v3 passwords become resource macros, never literals

Pure functions and an in-memory database; no Nagios runs.
"""
import pytest

from app.network_discovery import device_plugin_variables as dpv
from app.network_discovery.plugin_registry import (
    PluginConfigurationError,
    SnmpV3Error,
    Transport,
    command_definition_name,
    editable_variables,
    plugin_for_command,
    render_command_definition,
    resolve_plugin_command,
)

PASSWORD = "synthetic-auth-secret"
PRIVACY = "synthetic-priv-secret"

V3_AUTHPRIV = {
    "protocol": "3", "security_level": "authPriv", "v3_user": "monitor",
    "auth_protocol": "SHA", "auth_password": PASSWORD,
    "priv_protocol": "AES", "priv_password": PRIVACY,
}


# ==========================================================
# REGISTRY
# ==========================================================

class TestRegistry:

    def test_v2c_and_default_commands_are_unchanged(self):
        variables = {"port": 161, "community": "public", "oid": "1.3.6.1.2.1.1.3.0"}
        assert resolve_plugin_command("snmp", variables, Transport.UDP) == (
            "pinpoint_nd_snmp!161!public!1.3.6.1.2.1.1.3.0!"
        )
        assert resolve_plugin_command("snmp", {**variables, "protocol": "2c"}, Transport.UDP) == (
            "pinpoint_nd_snmp!161!public!1.3.6.1.2.1.1.3.0!-P '2c'"
        )

    def test_only_version_3_selects_the_v3_command(self):
        assert command_definition_name("snmp", {"protocol": "3"}) == "snmp_v3"
        assert command_definition_name("snmp", {"protocol": "2c"}) == "snmp"
        assert command_definition_name("snmp", {}) == "snmp"
        assert command_definition_name("ssh", {"protocol": "3"}) == "ssh"

    def test_v3_command_carries_options_and_slot_flags(self):
        command = resolve_plugin_command("snmp_v3", {**V3_AUTHPRIV, "port": 161, "oid": "1.3.6.1"}, Transport.UDP)
        assert command.startswith("pinpoint_nd_snmp_v3!161!1.3.6.1!")
        for flag in ("-L 'authPriv'", "-U 'monitor'", "-a 'SHA'", "-x 'AES'", "--auth-slot", "--priv-slot"):
            assert flag in command
        assert "-C" not in command

    def test_v3_definition_has_no_community_argument_and_fixes_protocol(self):
        line = render_command_definition("snmp_v3")
        assert "-P 3" in line and "-C" not in line and "check_snmp" in line

    def test_status_maps_the_v3_command_back_to_check_snmp(self):
        assert plugin_for_command("pinpoint_nd_snmp_v3!161!1.3!") == "check_snmp"

    @pytest.mark.parametrize("variable, value", [
        ("protocol", "4"), ("security_level", "none"), ("auth_protocol", "SHA512"),
        ("priv_protocol", "3DES"), ("v3_user", "-bad"), ("v3_user", "has space"),
    ])
    def test_enumerated_values_are_enforced(self, variable, value):
        with pytest.raises(PluginConfigurationError):
            from app.network_discovery.plugin_registry import validate_variable_value
            validate_variable_value(variable, value)

    def test_editable_variables_hide_system_owned_values(self):
        assert {"port", "community", "protocol", "security_level", "v3_user", "auth_password"} <= editable_variables("snmp")
        assert not {"oid", "token", "metric_path"} & (editable_variables("snmp") | editable_variables("ncpa"))


# ==========================================================
# OVERRIDE VALIDATION
# ==========================================================

class TestValidateOverrides:

    def test_unknown_plugin_is_rejected(self):
        with pytest.raises(dpv.UnknownPlugin):
            dpv.validate_overrides("nope", {})

    def test_unknown_key_names_the_field(self):
        with pytest.raises(dpv.PluginVariableError) as error:
            dpv.validate_overrides("snmp", {"colour": "red"})
        assert error.value.field == "colour"

    def test_system_owned_key_is_unknown(self):
        with pytest.raises(dpv.PluginVariableError) as error:
            dpv.validate_overrides("ncpa", {"token": "x"})
        assert error.value.field == "token"

    @pytest.mark.parametrize("value", [["a"], {"a": 1}, True, 1.5])
    def test_only_text_and_whole_numbers_are_values(self, value):
        with pytest.raises(dpv.PluginVariableError) as error:
            dpv.validate_overrides("snmp", {"community": value})
        assert error.value.field == "community"

    def test_invalid_port_names_the_field(self):
        with pytest.raises(dpv.PluginVariableError) as error:
            dpv.validate_overrides("snmp", {"port": 70000})
        assert error.value.field == "port"

    @pytest.mark.parametrize("bad", ["a'b", "a!b", "a$b", "a;b", "a`b", "a\\b", "a\nb"])
    def test_forbidden_characters_are_rejected(self, bad):
        with pytest.raises(dpv.PluginVariableError) as error:
            dpv.validate_overrides("snmp", {"community": bad})
        assert error.value.field == "community"

    def test_v2c_override_is_kept_as_given(self):
        result = dpv.validate_overrides("snmp", {"protocol": "2c", "community": "lab"})
        assert result.variables == {"protocol": "2c", "community": "lab"}
        assert result.secrets == {} and result.clear_secrets == set()

    def test_blank_values_are_dropped(self):
        assert dpv.validate_overrides("snmp", {"community": "", "port": None}).variables == {}

    def test_v3_fields_and_secrets_are_dropped_when_not_version_3(self):
        result = dpv.validate_overrides("snmp", {"protocol": "2c", "v3_user": "x", "auth_password": PASSWORD},
                                        stored_secrets={"priv_password"})
        assert result.variables == {"protocol": "2c"}
        assert result.secrets == {}
        assert result.clear_secrets == {"auth_password", "priv_password"}

    def test_authpriv_needs_every_field_and_names_the_missing_one(self):
        for field in ("security_level", "v3_user", "auth_protocol", "auth_password", "priv_protocol", "priv_password"):
            given = {key: value for key, value in V3_AUTHPRIV.items() if key != field}
            with pytest.raises(dpv.PluginVariableError) as error:
                dpv.validate_overrides("snmp", given)
            assert error.value.field == field

    def test_stored_secret_satisfies_the_requirement(self):
        given = {key: value for key, value in V3_AUTHPRIV.items() if key not in ("auth_password", "priv_password")}
        result = dpv.validate_overrides("snmp", given, stored_secrets={"auth_password", "priv_password"})
        assert result.secrets == {}
        assert result.clear_secrets == set()

    def test_clearing_a_stored_secret_makes_it_missing(self):
        given = {key: value for key, value in V3_AUTHPRIV.items() if key not in ("auth_password", "priv_password")}
        with pytest.raises(dpv.PluginVariableError) as error:
            dpv.validate_overrides("snmp", given, stored_secrets={"auth_password", "priv_password"},
                                   clear_secrets=["priv_password"])
        assert error.value.field == "priv_password"

    def test_levels_below_authpriv_drop_what_they_do_not_use(self):
        result = dpv.validate_overrides("snmp", {**V3_AUTHPRIV, "security_level": "authNoPriv"})
        assert "priv_protocol" not in result.variables
        assert set(result.secrets) == {"auth_password"}
        assert "priv_password" in result.clear_secrets
        none = dpv.validate_overrides("snmp", {"protocol": "3", "security_level": "noAuthNoPriv", "v3_user": "u",
                                               "auth_password": PASSWORD})
        assert none.secrets == {} and "auth_protocol" not in none.variables

    @pytest.mark.parametrize("password", ["short", "x" * 65, " leading-space1", "tab\tinside1234", "quote'inside1234",
                                          "unicodé-password"])
    def test_weak_or_unsafe_passwords_are_rejected_without_echo(self, password):
        with pytest.raises(dpv.PluginVariableError) as error:
            dpv.validate_overrides("snmp", {**V3_AUTHPRIV, "auth_password": password})
        assert error.value.field == "auth_password"
        assert password not in str(error.value)

    def test_too_many_keys_are_rejected(self):
        with pytest.raises(dpv.PluginVariableError):
            dpv.validate_overrides("snmp", {f"k{i}": "x" for i in range(40)})

    def test_non_snmp_plugin_override(self):
        assert dpv.validate_overrides("http", {"url": "/health", "port": 8080}).variables == {"url": "/health", "port": 8080}


# ==========================================================
# STORAGE
# ==========================================================

class TestStorage:

    def test_secrets_are_encrypted_and_never_serialised(self, app):
        with app.app_context():
            result = dpv.validate_overrides("snmp", V3_AUTHPRIV)
            stored = dpv.build_stored(result, {})
            blob = repr(stored)
            assert PASSWORD not in blob and PRIVACY not in blob
            assert stored["auth_password_enc"].startswith("v1:")
            view = dpv.serialize(stored, "snmp")
            assert PASSWORD not in repr(view) and PRIVACY not in repr(view)
            assert view["secrets_set"] == {"auth_password": True, "priv_password": True}
            assert view["variables"]["v3_user"] == "monitor"
            assert dpv.decrypt_secrets(stored) == {"auth_password": PASSWORD, "priv_password": PRIVACY}

    def test_keeping_and_clearing_secrets(self, app):
        with app.app_context():
            first = dpv.build_stored(dpv.validate_overrides("snmp", V3_AUTHPRIV), {})
            keep = dpv.validate_overrides(
                "snmp", {k: v for k, v in V3_AUTHPRIV.items() if not k.endswith("_password")},
                stored_secrets=dpv.stored_secret_names(first))
            second = dpv.build_stored(keep, first)
            assert second["auth_password_enc"] == first["auth_password_enc"]
            changed = dpv.build_stored(dpv.validate_overrides(
                "snmp", {**V3_AUTHPRIV, "security_level": "authNoPriv"}, stored_secrets=dpv.stored_secret_names(first)), first)
            assert "priv_password_enc" not in changed

    def test_unreadable_secret_is_skipped_not_fatal(self, app):
        with app.app_context():
            assert dpv.decrypt_secrets({"auth_password_enc": "v1:garbage"}) == {}


# ==========================================================
# CONFIG GENERATION
# ==========================================================

import re
from pathlib import Path

from app.network_discovery.create_host_cfg import (
    _create_host_cfg_file,
    apply_secret_substitutions,
    collect_snmp_secrets,
    load_host_plugin_facts,
)
from tests.unit.test_create_host_cfg import make_device, make_host, patched_config

OID = "1.3.6.1.2.1.1.3.0"


def store_override(db_session, device, validated_input, previous=None):
    """Save an override like the API does (encrypting the passwords)."""
    validated = dpv.validate_overrides("snmp", validated_input)
    device.Plugin_Variables = {"snmp": dpv.build_stored(validated, previous or {})}
    db_session.session.commit()


def generate(app, device, tmp_path, host_name="snmp-host", ip="10.0.0.70"):
    discovered = {"10.0.0.0/24": {ip: make_host(
        host_name, udp={"161": "snmp"}, net_discovery_id=device.NetDiscoveryID,
        plugin_variables=device.Plugin_Variables)}}
    resource = tmp_path / "resource.cfg"
    if not resource.exists():
        resource.write_text("$USER1$=/usr/local/nagios/libexec\n")
        resource.chmod(0o660)
    with patched_config(app, HOST_CONFIG_DIR=tmp_path, NAGIOS_RESOURCE_CFG=str(resource),
                        SNMP_OIDS=[{"metric": "uptime", "oid": OID}], SNMP_COMMUNITY_STRING="public",
                        SNMP_PORT="161", NCPA_METRICS=[], NCPA_PORT="5693"):
        cfg = _create_host_cfg_file(discovered)
    return cfg.read_text(), resource.read_text()


@pytest.mark.usefixtures("monitoring_plugins")
class TestV3ConfigGeneration:

    def test_v3_passwords_become_slots_not_literals(self, app, db_session, admin_user, tmp_path):
        device = make_device(db_session, admin_user, "snmp-host", "10.0.0.70")
        store_override(db_session, device, V3_AUTHPRIV)
        hosts, resource = generate(app, device, tmp_path)

        assert PASSWORD not in hosts and PRIVACY not in hosts
        commands = re.findall(r"check_command\s+(pinpoint_nd_snmp_v3\S.*)", hosts)
        assert commands, hosts
        for command in commands:
            assert re.search(r"--auth-slot 'USER\d+'", command) and re.search(r"--priv-slot 'USER\d+'", command)
            assert "$USER" not in command and "-C " not in command
        assert f"={PASSWORD}" in resource and f"={PRIVACY}" in resource
        definition = re.search(r"command_name\s+pinpoint_nd_snmp_v3\s+command_line\s+(.*)", hosts)
        assert definition and "pinpoint_check_native.py" in definition.group(1)
        assert "-P 3" in definition.group(1)

    def test_v3_command_resolves_to_the_same_effective_check(self, app, db_session, admin_user, tmp_path):
        device = make_device(db_session, admin_user, "snmp-host", "10.0.0.70")
        store_override(db_session, device, V3_AUTHPRIV)
        hosts, _resource = generate(app, device, tmp_path)
        command = re.search(r"check_command\s+(pinpoint_nd_snmp_v3\S.*)", hosts).group(1)
        for expected in (f"!161!{OID}!", "-L 'authPriv'", "-U 'monitor'", "-a 'SHA'", "-x 'AES'"):
            assert expected in command

    def test_v2c_device_renders_exactly_as_before(self, app, db_session, admin_user, tmp_path):
        (tmp_path / "a").mkdir()
        (tmp_path / "b").mkdir()
        plain = make_device(db_session, admin_user, "snmp-host", "10.0.0.70")
        before, resource_before = generate(app, plain, tmp_path / "a")
        with_override = make_device(db_session, admin_user, "snmp-host", "10.0.0.71")
        store_override(db_session, with_override, {"protocol": "2c"})
        after, _ = generate(app, with_override, tmp_path / "b", ip="10.0.0.71")
        assert "pinpoint_nd_snmp_v3" not in before and "pinpoint_nd_snmp_v3" not in after
        assert f"!161!public!{OID}!" in before
        assert f"!161!public!{OID}!-P '2c'" in after
        assert "# BEGIN PINPOINT" not in resource_before

    def test_noauthnopriv_has_no_secrets_and_no_slot_flags(self, app, db_session, admin_user, tmp_path):
        device = make_device(db_session, admin_user, "snmp-host", "10.0.0.70")
        store_override(db_session, device, {"protocol": "3", "security_level": "noAuthNoPriv", "v3_user": "monitor"})
        hosts, resource = generate(app, device, tmp_path)
        command = re.search(r"check_command\s+(pinpoint_nd_snmp_v3\S.*)", hosts).group(1)
        assert "-L 'noAuthNoPriv'" in command and "slot" not in command
        assert "# BEGIN PINPOINT" not in resource

    def test_unreadable_password_skips_the_port_instead_of_rendering_without_it(self, app, db_session, admin_user, tmp_path):
        device = make_device(db_session, admin_user, "snmp-host", "10.0.0.70")
        store_override(db_session, device, V3_AUTHPRIV)
        device.Plugin_Variables = {"snmp": {**device.Plugin_Variables["snmp"], "auth_password_enc": "v1:garbage"}}
        db_session.session.commit()
        hosts, _resource = generate(app, device, tmp_path)
        assert "pinpoint_nd_snmp_v3" not in hosts and "check_snmp" not in hosts

    def test_switching_back_to_v2c_frees_the_slots_and_keeps_other_lines(self, app, db_session, admin_user, tmp_path):
        device = make_device(db_session, admin_user, "snmp-host", "10.0.0.70")
        store_override(db_session, device, V3_AUTHPRIV)
        _hosts, resource = generate(app, device, tmp_path)
        assert PASSWORD in resource and resource.startswith("$USER1$=/usr/local/nagios/libexec\n")

        store_override(db_session, device, {"protocol": "2c"})
        hosts, resource = generate(app, device, tmp_path)
        assert PASSWORD not in resource and PRIVACY not in resource
        assert resource == "$USER1$=/usr/local/nagios/libexec\n# BEGIN PINPOINT\n# END PINPOINT\n"
        assert "pinpoint_nd_snmp_v3" not in hosts

    def test_facts_hold_plaintext_only_for_version_3(self, app, db_session, admin_user):
        v3 = make_device(db_session, admin_user, "v3-host", "10.0.0.70")
        store_override(db_session, v3, V3_AUTHPRIV)
        v2 = make_device(db_session, admin_user, "v2-host", "10.0.0.71")
        store_override(db_session, v2, {"protocol": "2c"})
        facts = load_host_plugin_facts()
        assert facts[v3.NetDiscoveryID]["snmp"]["auth_password"] == PASSWORD
        assert v2.NetDiscoveryID not in facts
        assert collect_snmp_secrets(facts) == {
            f"snmp_v3:{v3.NetDiscoveryID}:auth_password": PASSWORD,
            f"snmp_v3:{v3.NetDiscoveryID}:priv_password": PRIVACY,
        }

    def test_substitution_fails_closed_without_a_slot(self):
        command = "pinpoint_nd_snmp_v3!161!1.3!-L 'authPriv' --auth-slot 'literal-password'"
        with pytest.raises(PluginConfigurationError):
            apply_secret_substitutions(command, {})
        assert apply_secret_substitutions(command, {"literal-password": "$USER4$"}).endswith("--auth-slot 'USER4'")

    def test_public_arguments_matching_a_password_are_not_replaced(self):
        command = "pinpoint_nd_snmp_v3!161!1.3!-U 'secretvalue' --auth-slot 'secretvalue'"
        result = apply_secret_substitutions(command, {"secretvalue": "$USER4$"})
        assert "-U 'secretvalue'" in result and "--auth-slot 'USER4'" in result
