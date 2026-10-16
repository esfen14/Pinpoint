"""
Per-device plugin variable overrides: validation, secret storage and serialisation for the
API behind the Device Inventory SNMP form (app/api/system/device_plugin_variables.py).

An override is stored in NetworkDiscovery.Plugin_Variables[<plugin>] and sits above the plugin's
defaults and the Settings values when the Nagios config is built (resolve_plugin_variables in
plugin_registry.py). This module only decides what may be stored there.

Secrets (SNMP v3 passwords) are encrypted with secrets_store under "<name>_enc" in the same
object. They are never returned: serialize() reports only whether each one is set. They are
decrypted by create_host_cfg.load_host_plugin_facts, written to a resource-macro slot and
referenced by slot identifier in the Nagios command, so they never reach hosts.cfg.

Validation reuses the registry's own rules (validate_variable_value, the SNMP v3 requirements),
so what the API accepts is exactly what the config generator will render.

Security: error messages name the field, never the value.
"""
from dataclasses import dataclass, field

from flask import current_app

from app import secrets_store
from app.network_discovery.plugin_registry import (
    PluginConfigurationError,
    SNMP_V3_FIELDS,
    SnmpV3Error,
    editable_variables,
    get_plugin_definition,
    snmp_v3_requirements,
    validate_snmp_password,
    validate_snmp_v3,
    validate_variable_value,
)

SECRET_SUFFIX = "_enc"
MAX_VARIABLES = 20
MAX_VALUE_LENGTH = 128


class PluginVariableError(ValueError):
    """An override is not acceptable. field names the variable (None when it is not about one); the message holds no value."""

    def __init__(self, message, field=None):
        super().__init__(message)
        self.field = field


class UnknownPlugin(PluginVariableError):
    """The plugin is not a registry definition."""


@dataclass
class ValidatedOverrides:
    """variables are the plain values to store, secrets the new plaintext passwords, clear_secrets the stored ones to remove."""
    variables: dict = field(default_factory=dict)
    secrets: dict = field(default_factory=dict)
    clear_secrets: set = field(default_factory=set)


def secret_names(plugin_name):
    """The credential variables of a registry plugin, as a set."""
    return set(get_plugin_definition(plugin_name).secret_variables)


def stored_secret_names(stored):
    """The secrets that have a value in a stored override object."""
    return {key[:-len(SECRET_SUFFIX)] for key, value in (stored or {}).items()
            if key.endswith(SECRET_SUFFIX) and value}


def clean_value(name, value):
    """Return value as the text/whole number to store for variable name, or raise PluginVariableError naming it."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise PluginVariableError(f"Variable '{name}' must be text or a whole number.", name)
    if len(str(value)) > MAX_VALUE_LENGTH:
        raise PluginVariableError(f"Variable '{name}' is too long.", name)
    try:
        validate_variable_value(name, value)
    except SnmpV3Error as error:
        raise PluginVariableError(str(error), name) from None
    except PluginConfigurationError as error:
        raise PluginVariableError(str(error), name) from None
    return int(value) if name == "port" else value


def validate_overrides(plugin_name, variables, stored_secrets=(), clear_secrets=()):
    """
    Validate a device's override for one plugin and return ValidatedOverrides. variables is the
    flat {name: value} the administrator sent, secrets included; blank values mean "not set".
    stored_secrets are the secrets already saved (a secret that is not sent is kept) and
    clear_secrets those to remove. Raises UnknownPlugin or PluginVariableError (field set).

    For SNMP, version 3 needs the fields of its security level (plugin_registry.validate_snmp_v3);
    fields a level does not use, and every v3 field of a v1/v2c device, are dropped along with
    their stored passwords.
    """
    try:
        editable = editable_variables(plugin_name)
        secrets_allowed = secret_names(plugin_name)
    except PluginConfigurationError:
        raise UnknownPlugin(f"Unknown plugin '{plugin_name}'.") from None
    if not isinstance(variables, dict):
        raise PluginVariableError("variables must be an object.")
    if len(variables) > MAX_VARIABLES:
        raise PluginVariableError(f"At most {MAX_VARIABLES} variables can be set.")
    clear_secrets = set(clear_secrets or ())
    for name in clear_secrets:
        if name not in secrets_allowed:
            raise PluginVariableError(f"'{name}' is not a secret of this plugin.", "clear_secrets")

    plain, provided = {}, {}
    for name, value in variables.items():
        if name not in editable:
            raise PluginVariableError(f"Unknown variable '{name}'.", str(name))
        if value is None or value == "":
            continue
        if name in secrets_allowed:
            if not isinstance(value, str):
                raise PluginVariableError(f"Variable '{name}' must be text.", name)
            provided[name] = value
        else:
            plain[name] = clean_value(name, value)

    kept = (set(stored_secrets) - clear_secrets) | set(provided)
    if plugin_name == "snmp":
        plain, provided, kept = apply_snmp_rules(plain, provided, kept)

    dropped = (set(stored_secrets) | set(variables)) & secrets_allowed - kept
    return ValidatedOverrides(plain, provided, clear_secrets | dropped)


def apply_snmp_rules(plain, provided, kept):
    """
    Apply the SNMP version rules to cleaned values; return (variables, new secrets, secrets that
    stay set). Version 3 must be complete for its level; anything else loses its v3 fields.
    """
    if plain.get("protocol") != "3":
        return ({k: v for k, v in plain.items() if k not in SNMP_V3_FIELDS}, {}, set())
    try:
        needed = set(snmp_v3_requirements(plain.get("security_level")))
        validate_snmp_v3({**plain, **{name: "set" for name in kept}})
    except SnmpV3Error as error:
        raise PluginVariableError(str(error), error.field) from None
    for name, password in provided.items():
        if name not in needed:
            continue
        try:
            validate_snmp_password(password)
        except SnmpV3Error as error:
            raise PluginVariableError(str(error), name) from None
    keep_fields = needed | {"security_level"}
    return (
        {k: v for k, v in plain.items() if k not in SNMP_V3_FIELDS or k in keep_fields},
        {k: v for k, v in provided.items() if k in needed},
        kept & needed,
    )


def build_stored(validated, previous):
    """
    The object to store for an override: the plain variables plus every secret that stays set,
    encrypted. A secret that was not sent keeps its stored ciphertext. Raises
    secrets_store.SecretsError when the server has no fixed key.
    """
    stored = dict(validated.variables)
    for name in secret_names_of(validated, previous):
        if name in validated.secrets:
            stored[name + SECRET_SUFFIX] = secrets_store.encrypt(validated.secrets[name])
        elif name not in validated.clear_secrets and (previous or {}).get(name + SECRET_SUFFIX):
            stored[name + SECRET_SUFFIX] = previous[name + SECRET_SUFFIX]
    return stored


def secret_names_of(validated, previous):
    """Every secret name that may appear in a stored object: new ones and those already stored."""
    return set(validated.secrets) | stored_secret_names(previous)


def decrypt_secrets(stored):
    """
    {name: plaintext} of the readable secrets in a stored override object. One that can no longer
    be read (the key changed) is left out and logged by name only, so the planner skips the check.
    """
    result = {}
    for key, value in (stored or {}).items():
        if not key.endswith(SECRET_SUFFIX) or not value:
            continue
        name = key[:-len(SECRET_SUFFIX)]
        try:
            result[name] = secrets_store.decrypt(value)
        except secrets_store.SecretsError:
            current_app.logger.warning("A stored %s can no longer be read; re-enter it.", name)
    return result


def serialize(stored, plugin_name):
    """
    The override as the API returns it: {"plugin", "variables" (plain values only),
    "secrets_set" ({name: bool}), "editable" (the variables that may be set)}. No secret value.
    """
    stored = stored if isinstance(stored, dict) else {}
    present = stored_secret_names(stored)
    return {
        "plugin": plugin_name,
        "variables": {k: v for k, v in stored.items() if not k.endswith(SECRET_SUFFIX)},
        "secrets_set": {name: name in present for name in sorted(secret_names(plugin_name))},
        "editable": sorted(editable_variables(plugin_name)),
    }

