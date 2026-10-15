"""
Per-device plugin variables API: the overrides behind the Device Inventory SNMP form
(version, community, SNMP v3 user and credentials) and any other registry plugin's variables.

An override lives in NetworkDiscovery.Plugin_Variables[<plugin>] and wins over the plugin's
defaults and the Settings values when the Nagios config is built. Reading needs ``system.hosts``;
saving, resetting and testing need ``system.hosts.edit``. A change is written to the activity log
(variable names only, never values) and applied through the shared config writer, which validates
it with the Nagios binary; if Nagios rejects it the change is rolled back and the response is 422.

Secret variables (SNMP v3 passwords) are encrypted when stored and never returned: reads only say
whether each one is set. A secret that is not sent keeps its stored value; "clear_secrets" removes
one. The Nagios command references them by resource-slot identifier, so they never reach hosts.cfg.

Routes
------
GET    /system/hosts/<id>/plugin-variables/<plugin>
    The device's override for one registry plugin (no secret values).

PUT    /system/hosts/<id>/plugin-variables/<plugin>
    Replace the override. An empty body resets it.

DELETE /system/hosts/<id>/plugin-variables/<plugin>
    Reset the override: the device returns to the defaults.

POST   /system/hosts/<id>/plugin-variables/<plugin>/test
    Query the device once with the settings in the body (or the saved ones). Saves nothing.
"""
import sqlalchemy as sa
from flask import current_app, request
from flask_login import current_user, login_required

from app import db
from app.api.helper import error, success
from app.api.helper.database_access.permissions import require_permission
from app.api.system import system_bp
from app.api.system.device_identity import get_device_or_404
from app.logging.user_activity import create_user_log
from app.network_discovery import device_plugin_variables as variables_module
from app.network_discovery.device_identity import nagios_host_name
from app.network_discovery.interface_discovery import SNMP_PORT_FILTER
from app.network_discovery.plugin_registry import PluginConfigurationError, resolve_plugin_variables
from app.network_discovery.plugin_settings import plugin_config
from app.network_discovery.snmp_check import run_snmp_test
from app.secrets_store import SecretsError
from app.system_models import DeviceState, Open_UDP_Services, PortState

MAX_BODY_BYTES = 8 * 1024


# ==========================================================
# HELPERS
# ==========================================================

def plugin_or_404(plugin):
    """Return (plugin, None), or (None, error response) when plugin is not a registry plugin."""
    try:
        variables_module.secret_names(plugin)
    except PluginConfigurationError:
        return None, error(f"Unknown plugin '{plugin}'.", 404)
    return str(plugin).lower(), None


def editable_device(id, plugin):
    """Return (device, plugin, None) for a device whose overrides may be read, or (None, None, error response)."""
    plugin, problem = plugin_or_404(plugin)
    if problem is not None:
        return None, None, problem
    device, problem = get_device_or_404(id)
    if problem is not None:
        return None, None, problem
    return device, plugin, None


def refuse_inactive(device):
    """An error response for a retired or merged device (it is not in the Nagios config), else None."""
    if device.Device_State in (DeviceState.RETIRED, DeviceState.MERGED):
        return error("A retired or merged device is not monitored, so its plugin settings cannot be changed.", 400)
    return None


def field_error(exc):
    """The 400 response for a rejected value, with the offending variable in data.field."""
    return error(str(exc), 400, {"field": exc.field} if exc.field else None)


def parse_body(raw):
    """
    Split a request body into (variables, clear_secrets). None, an empty object or {"variables": {}}
    mean "no values". Raises PluginVariableError for anything that is not
    {"variables": {...}, "clear_secrets": [...]}.
    """
    if raw is None or raw == {}:
        return {}, []
    if not isinstance(raw, dict) or set(raw) - {"variables", "clear_secrets"}:
        raise variables_module.PluginVariableError("Send an object with variables and, optionally, clear_secrets.")
    clear = raw.get("clear_secrets", [])
    if not isinstance(clear, list) or not all(isinstance(name, str) for name in clear):
        raise variables_module.PluginVariableError("clear_secrets must be a list of names.", "clear_secrets")
    return raw.get("variables", {}), clear


def read_body():
    """The request's JSON body (None when it is absent or empty); raises PluginVariableError if it is too large or not JSON."""
    if (request.content_length or 0) > MAX_BODY_BYTES:
        raise variables_module.PluginVariableError("The request is too large.")
    if not request.get_data(cache=True):
        return None
    data = request.get_json(silent=True)
    if data is None:
        raise variables_module.PluginVariableError("The body must be a JSON object.")
    return data


def change_description(plugin, device, names):
    """The activity-log line for a change: plugin, device and the variable names, never the values."""
    listed = ", ".join(sorted(names)) if names else "none"
    return f"Updated {plugin} settings for device {nagios_host_name(device)} (variables: {listed})"


def apply_override(device, plugin, stored, description):
    """
    Save `stored` (or remove the override when it is empty) as the device's override for plugin,
    apply the Nagios config and commit. Returns None on success, or the error response after
    rolling the change back (422 when Nagios rejects it).
    """
    from app.network_discovery.create_host_cfg import config_write_lock, regenerate_and_apply_config_status
    try:
        with config_write_lock:
            current = dict(device.Plugin_Variables) if isinstance(device.Plugin_Variables, dict) else {}
            if stored:
                current[plugin] = stored
            else:
                current.pop(plugin, None)
            device.Plugin_Variables = current or None
            db.session.flush()
            status, message = regenerate_and_apply_config_status()
            if status == "failed":
                db.session.rollback()
                return error(f"The settings could not be applied: {message}", 422)
            create_user_log(current_user.UserID, description)
            db.session.commit()
            return None
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Could not save the device plugin variables.")
        return error("Unable to save the plugin settings.", 500)


def previous_override(device, plugin):
    """The stored override object of one plugin ({} when none)."""
    overrides = device.Plugin_Variables if isinstance(device.Plugin_Variables, dict) else {}
    stored = overrides.get(plugin)
    return stored if isinstance(stored, dict) else {}


# ==========================================================
# READ, SAVE, RESET
# ==========================================================

@system_bp.get('/hosts/<int:id>/plugin-variables/<plugin>')
@login_required
@require_permission('system.hosts')
def get_device_plugin_variables(id, plugin):
    """
    A device's override for one registry plugin: {"plugin", "variables" (plain values),
    "secrets_set" ({name: bool}, never a value), "editable" (the variables that may be set),
    "in_use" (snmp only: whether the device has an SNMP port monitored; null for other plugins)}.
    404 for an unknown device or plugin.
    """
    device, plugin, problem = editable_device(id, plugin)
    if problem is not None:
        return problem
    data = variables_module.serialize(previous_override(device, plugin), plugin)
    # The drawer shows the SNMP form only for a device that has an SNMP port monitored.
    data["in_use"] = device_snmp_port(device) is not None if plugin == "snmp" else None
    return success(data)


@system_bp.put('/hosts/<int:id>/plugin-variables/<plugin>')
@login_required
@require_permission('system.hosts.edit')
def update_device_plugin_variables(id, plugin):
    """
    Replace a device's override for one registry plugin. The plain variables sent replace the
    stored ones; a secret that is not sent keeps its stored value. An empty body resets the override.

    JSON Format
    {
        "variables": {"protocol": "3", "security_level": "authPriv", "v3_user": "monitor",
                      "auth_protocol": "SHA", "auth_password": "...",
                      "priv_protocol": "AES", "priv_password": "..."},
        "clear_secrets": ["priv_password"]
    }
    Errors: 400 with data.field naming the variable (unknown key, invalid value, a v3 field the
    security level needs), 404 unknown device or plugin, 422 when Nagios rejects the config (the
    change is rolled back). SNMP v1/v2c devices keep the command they always had.
    """
    device, plugin, problem = editable_device(id, plugin)
    if problem is not None:
        return problem
    problem = refuse_inactive(device)
    if problem is not None:
        return problem
    try:
        variables, clear = parse_body(read_body())
        previous = previous_override(device, plugin)
        validated = variables_module.validate_overrides(
            plugin, variables, stored_secrets=variables_module.stored_secret_names(previous), clear_secrets=clear)
        stored = variables_module.build_stored(validated, previous)
    except variables_module.PluginVariableError as exc:
        return field_error(exc)
    except SecretsError as exc:
        return error(exc.message, 400)

    names = set(stored) | set(validated.secrets)
    problem = apply_override(device, plugin, stored, change_description(plugin, device, {n.removesuffix("_enc") for n in names}))
    if problem is not None:
        return problem
    return success(variables_module.serialize(stored, plugin), message="Plugin settings saved.")


@system_bp.delete('/hosts/<int:id>/plugin-variables/<plugin>')
@login_required
@require_permission('system.hosts.edit')
def reset_device_plugin_variables(id, plugin):
    """Reset a device's override for one registry plugin: it returns to the defaults. No body."""
    device, plugin, problem = editable_device(id, plugin)
    if problem is not None:
        return problem
    problem = refuse_inactive(device)
    if problem is not None:
        return problem
    problem = apply_override(device, plugin, {}, f"Reset {plugin} settings of device {nagios_host_name(device)} to the defaults")
    if problem is not None:
        return problem
    return success(variables_module.serialize({}, plugin), message="Plugin settings reset.")


# ==========================================================
# TEST
# ==========================================================

def device_snmp_port(device):
    """The SNMP port monitored on the device, or None when it has none."""
    row = db.session.scalar(
        sa.select(Open_UDP_Services).where(
            Open_UDP_Services.NetDiscoveryID == device.NetDiscoveryID,
            SNMP_PORT_FILTER,
            Open_UDP_Services.Port_State.in_((PortState.MONITORED, PortState.MISSING)),
        ).order_by(Open_UDP_Services.Port_Number)
    )
    return row.Port_Number if row else None


@system_bp.post('/hosts/<int:id>/plugin-variables/<plugin>/test')
@login_required
@require_permission('system.hosts.edit')
def test_device_plugin(id, plugin):
    """
    Query the device once over SNMP with the settings in the body, or the saved ones when the
    body is empty, and report whether it answered. Nothing is saved or applied. Passwords left
    blank use the stored ones.

    JSON Format (all optional)
    {"variables": {"protocol": "3", "security_level": "authPriv", "v3_user": "monitor", ...}}

    Responds 200 with {"ok": bool, "state": "OK|WARNING|CRITICAL|UNKNOWN", "message": str}; an
    unreachable device is a failed result, not an error. 400 data.field names an invalid variable,
    or the plugin is not snmp (the only plugin with a test).
    """
    device, plugin, problem = editable_device(id, plugin)
    if problem is not None:
        return problem
    if plugin != "snmp":
        return error("Only SNMP settings can be tested.", 400)
    problem = refuse_inactive(device)
    if problem is not None:
        return problem
    try:
        raw = read_body()
        previous = previous_override(device, plugin)
        if raw is None or raw == {}:
            override = {key: value for key, value in previous.items() if not key.endswith(variables_module.SECRET_SUFFIX)}
            secrets = variables_module.decrypt_secrets(previous)
        else:
            variables, clear = parse_body(raw)
            validated = variables_module.validate_overrides(
                plugin, variables, stored_secrets=variables_module.stored_secret_names(previous), clear_secrets=clear)
            override = validated.variables
            kept = variables_module.decrypt_secrets(previous)
            secrets = {name: value for name, value in kept.items() if name not in validated.clear_secrets}
            secrets.update(validated.secrets)
    except variables_module.PluginVariableError as exc:
        return field_error(exc)

    port = device_snmp_port(device)
    resolved = resolve_plugin_variables(
        plugin, plugin_config(), discovered={"port": port} if port else None, overrides=override)
    if str(resolved.get("protocol") or "") == "3":
        try:
            from app.network_discovery.plugin_registry import validate_snmp_v3
            validate_snmp_v3({**resolved, **secrets})
        except PluginConfigurationError as exc:
            return error(str(exc), 400, {"field": getattr(exc, "field", None)})
    return success(run_snmp_test(device.IP_Address, resolved, secrets))
