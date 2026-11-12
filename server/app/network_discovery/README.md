# `app/network_discovery/` — scanning and Nagios configuration

Finds devices on the approved networks (`PINPOINT_NETWORKS`), identifies them,
and generates the validated Nagios host and service configuration. Imported by
`app/api/system/network_discovery.py` and the scheduler; not run directly.

| Module | Does |
|---|---|
| `network_discovery.py` | The scan itself (nmap) and per-host results |
| `create_host_cfg.py` | Builds and writes `hosts.cfg`, validates it with `nagios -v`, reloads Nagios |
| `host_config_templates.py`, `templates/*.tpl` | Jinja templates for hosts, services, contacts, escalations and event-handler commands |
| `plugin_registry.py`, `snmp_check.py`, `custom_checks.py`, `resource_macros.py` | Which checks each device gets (SNMP, NCPA, plugin-driven, custom) and how their secrets reach Nagios |
| `device_identity.py`, `identity_probes.py` | Decide whether a scanned address is a known device |
| `interface_discovery.py` | Reads a device's SNMP interfaces for the Device Inventory monitor choice |
| `port_lifecycle.py`, `ncpa_relocation.py`, `service_name_migration.py` | Port archiving and service moves |
| `discovery_settings.py`, `plugin_settings.py`, `device_plugin_variables.py`, `recipient_groups.py` | Settings that feed the generated configuration |

Who runs it: an administrator, from the Network Discovery and Device Inventory
pages; the scheduler runs rescans. A scan touches real networks and Nagios, so
tests use mocks or temporary paths. Never add localhost to `PINPOINT_NETWORKS`.

Behavior is specified in
[Data Model and Integrations](../../../spec%20files/Data_Model_and_Integrations.md)
and [Device Inventory Requirements](../../../spec%20files/Device_Inventory_Requirements.md).
