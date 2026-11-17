"""
Generate docs/reference/ERD.md from the SQLAlchemy models.

The output has two parts, both Mermaid ``erDiagram`` blocks:

* an overview with every table and every relationship but no columns, for skimming;
* one diagram per domain with every column, its type and its keys, for detail.

The tables come from the metadata of system_models.py, plugin_models.py and
history_models.py, so the file cannot drift from the code: a unit test
(tests/unit/test_erd_doc.py) fails when the committed file differs from what this
script produces, or when a table has no domain in DOMAINS below.

Usage, from server/ with the virtual environment active
-------------------------------------------------------
    python scripts/generate_erd.py            write docs/reference/ERD.md
    python scripts/generate_erd.py --check    exit 1 if the file is stale

No database is opened: only the table definitions are read.
"""
import os
import re
import sys

SERVER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = os.path.dirname(SERVER_DIR)
ERD_PATH = os.path.join(REPO_DIR, "docs", "reference", "ERD.md")

# Importing the app builds it and reads its configuration. Give it throwaway values
# so generating the diagram never needs, or touches, a real database or secret.
os.environ.setdefault("SECRET_KEY", "erd-generation-only")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("HISTORY_DATABASE_URL", "sqlite:///:memory:")
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

# ==========================================================
# DOMAINS
# ==========================================================
# Every table must appear in exactly one domain (the unit test enforces this), so a
# new table forces a decision about where it belongs. Order is the order in ERD.md.

DOMAINS = [
    ("Accounts and access", [
        "PERMISSION", "ROLE", "ROLE_PERMISSION", "USER", "USER_PREFERENCES",
        "PASSWORD_RESET_REQUEST",
    ]),
    ("Settings", [
        "SYSTEM_SETTINGS", "SMTP_SETTINGS", "PLUGIN_SETTINGS", "NOTIFICATION_POLICY",
        "NETWORK_PROFILE", "DISCOVERY_SETTINGS",
    ]),
    ("Audit log", [
        "ACTIVITY_LOG", "CONFIGURATION_CHANGES", "EXPORT_LOG",
    ]),
    ("Discovery and devices", [
        "NETWORK_DISCOVERY_STATUS", "SKIPPED_SERVICE", "NETWORK_DISCOVERY",
        "OPEN_TCP_Services", "OPEN_UDP_Services", "DEVICE_PARENT", "DEVICE_IDENTIFIER",
        "DEVICE_ADDRESS_HISTORY", "DEVICE_INTERFACE", "DEVICE_REVIEW_ITEM",
    ]),
    ("NCPA deployment", [
        "SSH_CREDENTIALS", "NCPA_DEPLOYMENT_STATUS", "NCPA_DEPLOYMENT_RESULT",
        "NCPA_DEPLOYMENT", "NCPA_DEVICE_PARTITION",
    ]),
    ("Alerts, maintenance and forecasts", [
        "ALERT_ACKNOWLEDGEMENT", "ACK_HISTORY", "NOTIFICATION_CURSOR",
        "HOST_ALERT_RECIPIENT", "ESCALATION", "MAINTENANCE_WINDOW",
        "MAINTENANCE_OCCURRENCE", "RESOURCE_FORECAST",
    ]),
    ("Plugins", [
        "PLUGIN", "PLUGIN_VERSION", "PLUGIN_COMMAND", "PLUGIN_COMMAND_OVERRIDE",
        "PLUGIN_DEPENDENCY", "PLUGIN_CONFIGURATION", "PLUGIN_HISTORY",
        "PLUGIN_SCAN_STATUS",
    ]),
    ("Remediation", [
        "REMEDIATION_ACTION", "REMEDIATION_RUN", "REMEDIATION_CONSUMER_STATE",
    ]),
    ("Nagios history (history.db)", [
        "HOST_STATUS", "HOST_PERF_DATA", "SERVICE_STATUS", "SERVICE_PERF_DATA",
        "PROGRAM_STATUS",
    ]),
]

PURPOSES = {
    "Accounts and access": "Users, roles and permissions, per-user display preferences and password-reset requests.",
    "Settings": "Singleton and per-plugin settings: system, email, notification policy, network profile and discovery.",
    "Audit log": "Who did what: the activity log and the configuration-change and export records attached to it.",
    "Discovery and devices": "Scan runs, discovered devices and their services, identity evidence, address history, interfaces and manual parent links.",
    "NCPA deployment": "Stored SSH trust, each remote NCPA install run, and each device's installed agent state.",
    "Alerts, maintenance and forecasts": "Acknowledgements, notification cursors, alert recipients, escalations, maintenance windows and resource forecasts.",
    "Plugins": "Plugin Manager: plugin definitions, versions, commands, dependencies and which targets each plugin monitors.",
    "Remediation": "Automatic-recovery rules, the run recorded for each decision, and the consumer's heartbeat.",
    "Nagios history (history.db)": "Polled Nagios status snapshots in the separate history database; no foreign keys to system.db.",
}

# SQLAlchemy type class names mapped to short, Mermaid-safe names.
TYPE_NAMES = {
    "integer": "int",
    "biginteger": "bigint",
    "smallinteger": "smallint",
    "string": "string",
    "text": "text",
    "boolean": "bool",
    "datetime": "datetime",
    "date": "date",
    "time": "time",
    "float": "float",
    "numeric": "decimal",
    "json": "json",
    "enum": "enum",
    "largebinary": "blob",
}

MERMAID_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


# ==========================================================
# READING THE MODELS
# ==========================================================

def collect_tables():
    """
    Return {table name: SQLAlchemy Table} for every model on every bind.

    Importing the model modules registers their tables on ``db.metadatas`` (the
    default bind plus the ``history`` bind). No database connection is made.
    """
    from app import db
    import app.system_models  # noqa: F401
    import app.plugin_models  # noqa: F401
    import app.history_models  # noqa: F401

    tables = {}
    for metadata in db.metadatas.values():
        for table_name, table in metadata.tables.items():
            tables[table_name] = table
    return tables


def type_name(column):
    """Return the short Mermaid-safe type name for a column."""
    class_name = column.type.__class__.__name__.lower()
    if class_name in TYPE_NAMES:
        return TYPE_NAMES[class_name]
    # Unmapped types still render, under their lowercase SQLAlchemy class name.
    return re.sub(r"[^a-z0-9_]", "", class_name) or "unknown"


def column_keys(table, column):
    """Return the Mermaid key markers for a column: PK, FK and/or UK."""
    keys = []
    if column.primary_key:
        keys.append("PK")
    if len(column.foreign_keys) > 0:
        keys.append("FK")
    if column.unique and not column.primary_key:
        keys.append("UK")
    return keys


def check_name(name, what):
    """Raise if a table or column name would not render in Mermaid."""
    if not MERMAID_NAME.match(name):
        raise ValueError(f"{what} {name!r} is not a Mermaid-safe name")


def relationships(tables):
    """
    Return one (parent, child, column name, optional) tuple per foreign key.

    ``optional`` is true when the foreign-key column accepts NULL, so the parent
    side is drawn as zero-or-one instead of exactly one.
    """
    found = []
    for table_name in sorted(tables):
        table = tables[table_name]
        for column in table.columns:
            for foreign_key in column.foreign_keys:
                parent_name = foreign_key.column.table.name
                optional = bool(column.nullable) and not column.primary_key
                found.append((parent_name, table_name, column.name, optional))
    return found


def relationship_line(parent, child, column_name, optional):
    """Return the Mermaid line for one foreign key (many children per parent)."""
    parent_end = "|o" if optional else "||"
    return f'  {parent} {parent_end}--o{{ {child} : "{column_name}"'


# ==========================================================
# RENDERING
# ==========================================================

def render_overview(tables, all_relationships):
    """Return the overview block: every table and relationship, no columns."""
    lines = ["```mermaid", "erDiagram"]
    linked = set()
    for parent, child, column_name, optional in all_relationships:
        lines.append(relationship_line(parent, child, column_name, optional))
        linked.add(parent)
        linked.add(child)
    for table_name in sorted(tables):
        if table_name not in linked:
            lines.append(f"  {table_name}")
    lines.append("```")
    return "\n".join(lines)


def render_domain(domain_tables, tables, all_relationships):
    """Return one domain block: its tables with columns and its relationships."""
    in_domain = set(domain_tables)
    lines = ["```mermaid", "erDiagram"]
    for table_name in domain_tables:
        table = tables[table_name]
        lines.append(f"  {table_name} {{")
        for column in table.columns:
            check_name(column.name, f"column of {table_name}")
            parts = [type_name(column), column.name]
            keys = column_keys(table, column)
            if keys:
                parts.append(",".join(keys))
            line = "    " + " ".join(parts)
            if column.nullable and not column.primary_key:
                line += ' "nullable"'
            lines.append(line)
        lines.append("  }")
    outside = []
    for parent, child, column_name, optional in all_relationships:
        if child in in_domain:
            lines.append(relationship_line(parent, child, column_name, optional))
            for name in (parent, child):
                if name not in in_domain and name not in outside:
                    outside.append(name)
    lines.append("```")
    return "\n".join(lines), outside


def build_erd_markdown():
    """Return the complete text of docs/reference/ERD.md."""
    tables = collect_tables()
    for table_name in tables:
        check_name(table_name, "table")
    all_relationships = relationships(tables)

    out = []
    out.append("# Entity relationship diagram")
    out.append("")
    out.append("<!-- Generated by server/scripts/generate_erd.py from the SQLAlchemy models. -->")
    out.append("<!-- Do not edit by hand; run `python scripts/generate_erd.py` from server/. -->")
    out.append("")
    out.append(
        "Generated from `system_models.py`, `plugin_models.py` and `history_models.py`; "
        f"{len(tables)} tables. A unit test (`server/tests/unit/test_erd_doc.py`) fails "
        "when this file differs from the models, so it is always current."
    )
    out.append("")
    out.append(
        "Application tables live in `system.db`. The five Nagios snapshot tables live "
        "in `history.db` and have no foreign keys to `system.db`. Models: "
        "[Data_Model_and_Integrations.md](../../spec%20files/Data_Model_and_Integrations.md)."
    )
    out.append("")
    out.append("How to read it:")
    out.append("")
    out.append("- A line between two tables is a foreign key, labelled with the column. "
               "`||--o{` is one parent to many children; `|o--o{` means the column may be NULL.")
    out.append("- In the detail diagrams `PK` is a primary key, `FK` a foreign key and `UK` a "
               "unique column. A column marked \"nullable\" accepts NULL.")
    out.append("- A detail diagram draws the foreign keys that start in its own tables, so a "
               "referenced table from another domain appears without columns. Foreign keys "
               "pointing in from other domains are in the Overview.")
    out.append("")
    out.append("## Overview")
    out.append("")
    out.append("Every table and relationship, without columns.")
    out.append("")
    out.append(render_overview(tables, all_relationships))
    out.append("")

    for domain_name, domain_tables in DOMAINS:
        block, outside = render_domain(domain_tables, tables, all_relationships)
        out.append(f"## {domain_name}")
        out.append("")
        out.append(PURPOSES[domain_name])
        out.append("")
        out.append("Tables: " + ", ".join(domain_tables) + ".")
        if outside:
            out.append("")
            out.append("References tables of other domains (drawn without columns): " + ", ".join(outside) + ".")
        out.append("")
        out.append(block)
        out.append("")
    return "\n".join(out)


def main(argv):
    """Write ERD.md, or with --check report whether the committed file is current."""
    text = build_erd_markdown()
    if "--check" in argv:
        current = ""
        if os.path.exists(ERD_PATH):
            with open(ERD_PATH, encoding="utf-8") as handle:
                current = handle.read()
        if current != text:
            print("docs/reference/ERD.md is stale; run: python scripts/generate_erd.py")
            return 1
        print("docs/reference/ERD.md is current")
        return 0
    with open(ERD_PATH, "w", encoding="utf-8") as handle:
        handle.write(text)
    print(f"wrote {ERD_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
