"""
Resource-macro writer for PinPoint Network Diagnosis System.

Nagios resource files define $USER1$..$USER256$ macros, which can be used in
command definitions to keep literal secret values out of generated object configuration. Nagios
expands macros before execution; macros alone do not hide process arguments.  $USER1$ is conventionally the plugin directory;
PinPoint uses $USER2$..$USER256$ (255 slots) for its own secrets.

Public API
──────────
  allocate(secrets, *, existing=None)
      Given {key: plaintext_value} return {key: "$USERn$"}.  Slot numbers are
      stable: an existing assignment (from a previous call) is preserved and new
      keys fill the next unused slot.  Raises ResourceMacroLimitError when more
      than 255 distinct slots would be needed.

  write_resource_block(resource_cfg_path, slot_map, values)
      Replace (or create) the PinPoint-owned block inside resource_cfg_path with
      one "$USERn$=<value>" line per entry in slot_map/values.  Content outside
      the "# BEGIN PINPOINT" / "# END PINPOINT" markers is preserved exactly.
      The file is written atomically (temp file + os.replace) and preserves
      the existing owner, group and mode. An ownership change that the process
      cannot perform aborts the write before replacement.

  read_resource_block(resource_cfg_path)
      Parse the PinPoint block and return {slot_number (int): value (str)}.
      Returns an empty dict when the file does not exist or has no block.

  reclaim(keys_to_remove, slot_map)
      Return a new slot map with the listed keys removed.  The original dict is
      not mutated.  Silently ignores keys that are not in slot_map.

  restore_resource_cfg(backup_path, resource_cfg_path)
      Copy backup_path over resource_cfg_path to roll back a failed write.
      Raises FileNotFoundError / OSError on missing or unreadable backup.

Security notes
──────────────
  - Secret values must not be logged or included in exception messages.
  - The caller owns the resource.cfg path; this module never constructs it from
    untrusted input.
  - FORBIDDEN_VALUE_CHARACTERS from plugin_registry applies to all values.
"""

import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Dict, Iterable, Optional

from app.network_discovery.plugin_registry import FORBIDDEN_VALUE_CHARACTERS

# ── Constants ─────────────────────────────────────────────────────────────────

# Nagios $USER1$ is reserved for the plugin directory by convention.
FIRST_SLOT = 2
LAST_SLOT = 256
MAX_SLOTS = LAST_SLOT - FIRST_SLOT + 1  # 255

_BLOCK_BEGIN = "# BEGIN PINPOINT"
_BLOCK_END = "# END PINPOINT"

# File permission: group-readable (nagios group) but not world-readable.
_FILE_MODE = 0o660


# ── Exceptions ────────────────────────────────────────────────────────────────

class ResourceMacroLimitError(Exception):
    """
    Raised when allocating a new slot would exceed the 255 available resource
    macro slots ($USER2$..$USER256$).  The message says how many were requested
    and what the limit is, without including any secret values.
    """


# ── Public API ────────────────────────────────────────────────────────────────

def allocate(
    secrets: Dict[str, str],
    *,
    existing: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """
    Return {key: "$USERn$"} for each key in *secrets*.

    Slot assignment is stable: if *existing* is supplied (the result of a
    previous call), any key already present keeps its slot.  New keys fill the
    next unused slot in ascending order.

    Keys are arbitrary strings (e.g. "ncpa_token:42", "custom_check:7:password").
    Values in *secrets* are only used to validate that they don't contain
    FORBIDDEN_VALUE_CHARACTERS (values never leave this function or appear in
    exceptions).

    Raises ResourceMacroLimitError when the combined number of distinct slots
    (existing + new) would exceed MAX_SLOTS (255).
    """
    if not secrets and not existing:
        return {}

    # Start from the existing assignments.
    result: Dict[str, str] = dict(existing or {})

    # Validate values (but never include them in error messages).
    for key, value in secrets.items():
        bad = set(str(value)) & FORBIDDEN_VALUE_CHARACTERS
        if bad:
            raise ValueError(
                f"Secret value for key '{key}' contains a character forbidden in "
                "Nagios config/commands."
            )

    # Add any new keys.
    new_keys = [k for k in secrets if k not in result]
    if not new_keys:
        return result

    # Find slots already in use.
    used_slots = {_slot_number(macro) for macro in result.values()}

    # Pick the lowest unused slot for each new key.
    free = (n for n in range(FIRST_SLOT, LAST_SLOT + 1) if n not in used_slots)
    for key in sorted(new_keys):  # sorted for determinism across Python versions
        try:
            slot = next(free)
        except StopIteration:
            total_needed = len(result) + len(new_keys) - len(result.keys() & set(new_keys))
            raise ResourceMacroLimitError(
                f"Cannot allocate resource macro slot: all {MAX_SLOTS} slots "
                f"($USER{FIRST_SLOT}$..$USER{LAST_SLOT}$) are in use.  "
                f"Attempted to allocate {total_needed} total slots."
            )
        result[key] = f"$USER{slot}$"
        used_slots.add(slot)

    total = len(result)
    if total > MAX_SLOTS:
        raise ResourceMacroLimitError(
            f"Cannot allocate resource macro slots: {total} slots requested but the "
            f"limit is {MAX_SLOTS} ($USER{FIRST_SLOT}$..$USER{LAST_SLOT}$)."
        )

    return result


def write_resource_block(
    resource_cfg_path: Path,
    slot_map: Dict[str, str],
    values: Dict[str, str],
) -> None:
    """
    Replace (or insert) the PinPoint-owned block in *resource_cfg_path*.

    The block is delimited by::

        # BEGIN PINPOINT
        $USERn$=<value>
        ...
        # END PINPOINT

    Content before "# BEGIN PINPOINT" and after "# END PINPOINT" is preserved
    exactly.  If the markers are absent, the block is appended at the end.

    The file is written atomically via a sibling temp file + os.replace so a
    crash or interrupt never leaves a partially-written file.  The final mode
    preserves the existing owner, group and permissions. New files use 0660.
    The temporary file starts private (0600); it receives the final metadata
    before replacement. Failure to preserve ownership aborts the update.

    Args:
        resource_cfg_path: Path to the resource.cfg file to update.
        slot_map: {key: "$USERn$"} as returned by allocate().
        values: {key: plaintext_value} — the secrets to write into each slot.
    """
    resource_cfg_path = Path(resource_cfg_path)

    original_stat = resource_cfg_path.stat() if resource_cfg_path.exists() else None

    # Read existing content (create an empty file if missing).
    if resource_cfg_path.exists():
        existing_text = resource_cfg_path.read_text()
    else:
        existing_text = ""

    # Split into before-block / (ignored old block) / after-block.
    before, after = _split_around_block(existing_text)

    # Build the new block lines.
    block_lines = [_BLOCK_BEGIN + "\n"]
    # Write in slot-number order so the file is deterministic.
    for key, macro in sorted(slot_map.items(), key=lambda kv: _slot_number(kv[1])):
        value = values.get(key, "")
        block_lines.append(f"{macro}={value}\n")
    block_lines.append(_BLOCK_END + "\n")

    new_text = before + "".join(block_lines) + after

    # A unique private sibling avoids predictable temporary paths and keeps
    # secret bytes unreadable while they are written.
    fd, name = tempfile.mkstemp(prefix=".pinpoint-resource-", dir=resource_cfg_path.parent)
    tmp_path = Path(name)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(new_text)
            stream.flush()
            if original_stat is not None:
                temp_stat = os.fstat(stream.fileno())
                if (temp_stat.st_uid, temp_stat.st_gid) != (original_stat.st_uid, original_stat.st_gid):
                    os.fchown(stream.fileno(), original_stat.st_uid, original_stat.st_gid)
            mode = stat.S_IMODE(original_stat.st_mode) if original_stat else _FILE_MODE
            os.fchmod(stream.fileno(), mode)
            os.fsync(stream.fileno())
        os.replace(tmp_path, resource_cfg_path)
    finally:
        tmp_path.unlink(missing_ok=True)


def read_resource_block(resource_cfg_path: Path) -> Dict[int, str]:
    """
    Parse the PinPoint-owned block in *resource_cfg_path* and return
    {slot_number (int): value (str)}.

    Only lines inside "# BEGIN PINPOINT" / "# END PINPOINT" are read.  Returns
    an empty dict when the file is missing, unreadable or has no PinPoint block.
    """
    resource_cfg_path = Path(resource_cfg_path)
    try:
        text = resource_cfg_path.read_text()
    except OSError:
        return {}

    _, block_text, _ = _extract_block(text)
    result: Dict[int, str] = {}
    for line in block_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        macro, _, value = line.partition("=")
        macro = macro.strip()
        if macro.startswith("$USER") and macro.endswith("$"):
            try:
                n = int(macro[5:-1])
            except ValueError:
                continue
            result[n] = value
    return result


def reclaim(
    keys_to_remove: Iterable[str],
    slot_map: Dict[str, str],
) -> Dict[str, str]:
    """
    Return a copy of *slot_map* with each key in *keys_to_remove* removed.
    The original *slot_map* is not mutated.  Keys absent from *slot_map* are
    silently ignored.
    """
    remove_set = set(keys_to_remove)
    return {k: v for k, v in slot_map.items() if k not in remove_set}


def restore_resource_cfg(backup_path: Path, resource_cfg_path: Path) -> None:
    """
    Copy *backup_path* back over *resource_cfg_path* to roll back a failed write.

    Raises FileNotFoundError / OSError when the backup is missing or unreadable.
    The backup file is not removed.
    """
    backup_path = Path(backup_path)
    resource_cfg_path = Path(resource_cfg_path)
    # This will raise FileNotFoundError if backup_path doesn't exist.
    shutil.copy2(str(backup_path), str(resource_cfg_path))


# ── Internal helpers ─────────────────────────────────────────────────────────

def _slot_number(macro: str) -> int:
    """Extract the integer n from "$USERn$"."""
    return int(macro[5:-1])


def _extract_block(text: str):
    """
    Split *text* into (before, block_body, after) where block_body is the
    text between (and not including) the BEGIN/END markers.  If no markers are
    found, block_body is empty and after is empty, before is the full text.
    """
    begin_idx = text.find(_BLOCK_BEGIN)
    if begin_idx == -1:
        return text, "", ""

    end_idx = text.find(_BLOCK_END, begin_idx)
    if end_idx == -1:
        # Malformed: BEGIN without END — treat everything from BEGIN as block.
        before = text[:begin_idx]
        block_body = text[begin_idx + len(_BLOCK_BEGIN):]
        return before, block_body, ""

    before = text[:begin_idx]
    block_body = text[begin_idx + len(_BLOCK_BEGIN): end_idx]
    after = text[end_idx + len(_BLOCK_END):]
    # Consume trailing newline after END marker so we don't double-newline.
    if after.startswith("\n"):
        after = after[1:]
    return before, block_body, after


def _split_around_block(text: str):
    """
    Return (before, after) where before is the text up to and including
    the newline before "# BEGIN PINPOINT" and after is the text starting
    immediately after "# END PINPOINT\n".  Both preserve the surrounding
    content exactly so the file is rewritten identically except for the block.
    """
    before, _block, after = _extract_block(text)
    # Ensure before ends with a newline so the BEGIN marker sits on its own line.
    if before and not before.endswith("\n"):
        before += "\n"
    return before, after
