"""
tests/unit/test_plugin_inventory_groups.py - The plugin inventory's `group` filter
(the Plugin Manager's category tabs).
"""
import pytest

from app.api.plugin import service
from app.plugin_models import Plugin, PluginSource, PluginStatus, PluginType

PLUGINS = [
    ("check_ssh", "Network Services"),
    ("check_dig", "DNS & Time"),
    ("check_dhcp", "Connectivity"),
    ("check_snmp", "SNMP & Devices"),
    ("check_ping", "Connectivity"),
    ("check_disk", "Storage"),
    ("check_mysql", "Database"),
    ("check_ldap", "Network Services"),
    ("check_by_ssh", "Network Services"),
    ("check_mailq", "Mail"),
    ("check_flexlm", "Utility"),
    ("check_cluster", "Utility"),
    ("check_dummy", "Utility"),
    ("custom_thing", None),
]


@pytest.fixture
def plugins(db_session):
    for name, category in PLUGINS:
        db_session.session.add(Plugin(
            Name=name, Category=category, Plugin_Type=PluginType.NAGIOS,
            Source=PluginSource.BASELINE_ISO, Status=PluginStatus.READY,
        ))
    db_session.session.commit()


def names(group):
    data = service.get_plugin_inventory(1, 50, "", None, None, "name", "asc", group=group)
    return [item["name"] for item in data["items"]]


@pytest.mark.usefixtures("plugins")
@pytest.mark.parametrize("group, expected", [
    ("Network Services", ["check_dhcp", "check_dig", "check_ssh"]),
    ("Device Availability", ["check_snmp"]),
    ("Network Protocols", ["check_ping"]),
    ("Servers", ["check_by_ssh", "check_cluster", "check_disk", "check_mailq"]),
    ("Application", ["check_flexlm", "check_ldap", "check_mysql"]),
    ("Other", ["check_dummy", "custom_thing"]),
])
def test_group_filters_to_its_tab(group, expected):
    assert names(group) == expected


@pytest.mark.usefixtures("plugins")
def test_no_group_returns_everything_and_tabs_partition_it():
    everything = names(None)
    tabs = [n for g in service.PLUGIN_GROUPS for n in names(g)]
    assert sorted(everything) == sorted(tabs) and len(everything) == len(PLUGINS)


def test_unknown_group_is_rejected():
    with pytest.raises(service.InvalidQueryError):
        names("Nonsense")
