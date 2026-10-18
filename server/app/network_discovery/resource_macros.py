"""Maintain protected Nagios resource slots and roll back failed config changes.

USER1 belongs to the plugin directory. Owned keys use USER2 through USER256,
excluding assignments outside the managed block. Check adapters consume slot
identifiers without expanding credentials into process arguments. Foreign-owned
production resources use the installer's restricted block writer on stdin.
"""

import json
import hashlib
import os
import re
import stat
import subprocess
import tempfile
from pathlib import Path

from app.network_discovery.plugin_registry import FORBIDDEN_VALUE_CHARACTERS

FIRST_SLOT = 2
LAST_SLOT = 256
MAX_SLOTS = LAST_SLOT - FIRST_SLOT + 1
_BLOCK_BEGIN = "# BEGIN PINPOINT"
_BLOCK_END = "# END PINPOINT"
_FILE_MODE = 0o660
_HELPER_RESOURCE_PATH = "/usr/local/nagios/etc/resource.cfg"
_HELPER_COMMAND = ["/usr/bin/sudo", "-n", "/usr/local/sbin/pinpoint-apply-resources"]
_MAX_HELPER_BYTES = 1024 * 1024
HELPER_REJECTED_MESSAGE = (
    "Protected resource helper rejected update. Check its installer setup and exact no-argument sudo rule, "
    "resource.cfg owner/group/mode (nagios:nagios 0660), and managed-block integrity; configuration was not applied."
)
HELPER_UNAVAILABLE_MESSAGE = (
    "Protected resource helper is unavailable or timed out. Verify installer setup and its exact no-argument "
    "sudo rule; configuration was not applied."
)


class ResourceMacroLimitError(ValueError):
    """There are insufficient unreserved resource slots for the desired keys."""


def _slot_number(macro):
    """Validate a managed macro reference and return its slot number."""
    match = re.fullmatch(r"\$USER([0-9]+)\$", str(macro))
    if not match or not FIRST_SLOT <= int(match.group(1)) <= LAST_SLOT:
        raise ValueError("Invalid managed resource macro slot.")
    return int(match.group(1))


def validate_values(values):
    """Reject secret values unsafe for Nagios configuration without echoing them."""
    for value in values.values():
        if not isinstance(value, str) or set(value) & FORBIDDEN_VALUE_CHARACTERS:
            raise ValueError("Secret contains a character forbidden in Nagios configuration.")


def allocate(secrets, *, existing=None, reserved=()):
    """Allocate stable slots, excluding external slots; no files are changed."""
    validate_values(secrets)
    result = dict(existing or {})
    used = {_slot_number(macro) for macro in result.values()}
    reserved = set(reserved)
    if len(used) != len(result) or used & reserved:
        raise ValueError("Managed resource macro slot assignments conflict.")
    new_keys = sorted(set(secrets) - set(result))
    free = [slot for slot in range(FIRST_SLOT, LAST_SLOT + 1) if slot not in used | reserved]
    if len(new_keys) > len(free):
        raise ResourceMacroLimitError(
            f"Resource macro slot limit exceeded: {len(result) + len(new_keys)} keys "
            f"requested; {MAX_SLOTS - len(reserved & set(range(FIRST_SLOT, LAST_SLOT + 1)))} slots available."
        )
    for key, slot in zip(new_keys, free):
        result[key] = f"$USER{slot}$"
    return result


def _extract_block(text):
    """Split the exact owned block; reject malformed or duplicate markers."""
    begins, ends = [], []
    offset = 0
    for line in text.splitlines(keepends=True):
        marker = line.rstrip("\r\n")
        if marker == _BLOCK_BEGIN:
            begins.append((offset, offset + len(line)))
        if marker == _BLOCK_END:
            ends.append((offset, offset + len(line)))
        offset += len(line)
    if not begins and not ends:
        return text, "", ""
    if len(begins) != 1 or len(ends) != 1 or ends[0][0] < begins[0][1]:
        raise ValueError("Malformed Pinpoint resource macro block.")
    return text[:begins[0][0]], text[begins[0][1]:ends[0][0]], text[ends[0][1]:]


def _split_around_block(text):
    """Return surrounding content, adding a separator only for an appended block."""
    before, _body, after = _extract_block(text)
    if before and not before.endswith("\n"):
        before += "\n"
    return before, after


def read_text(path):
    """Read without newline conversion; missing files have no assignments."""
    try:
        with Path(path).open(newline="") as stream:
            return stream.read()
    except FileNotFoundError:
        return ""


def read_reserved_slots(path):
    """Read slot numbers outside the owned block so allocation cannot overwrite them."""
    before, _body, after = _extract_block(read_text(path))
    return {int(slot) for slot in re.findall(r"^\s*\$USER([0-9]+)\$\s*=", before + after, re.M)}


def read_slot_assignments(path):
    """Read persisted key-to-slot metadata; values never enter the result."""
    _before, body, _after = _extract_block(read_text(path))
    result = {}
    for line in body.splitlines():
        match = re.fullmatch(r"# PINPOINT KEY (.+) (\$USER[0-9]+\$)", line)
        if match:
            try:
                key = json.loads(match.group(1))
            except ValueError:
                raise ValueError("Invalid resource slot metadata.") from None
            if not isinstance(key, str) or key in result:
                raise ValueError("Invalid resource slot metadata.")
            _slot_number(match.group(2))
            result[key] = match.group(2)
    if len(set(result.values())) != len(result):
        raise ValueError("Duplicate resource slot metadata.")
    return result


def replace_using_resource_helper(path, contents, metadata):
    """Send only an owned block on stdin to the fixed installer helper.

    Compare both external regions first; rollback cannot overwrite another
    owner's changes. The helper independently reads and checks their digest.
    Suppress all subprocess output and verify bytes and metadata after success.
    """
    if str(path) != _HELPER_RESOURCE_PATH:
        raise PermissionError("Ownership-preserving resource updates require the fixed installer destination.")
    desired = contents.decode("utf-8")
    before, _body, after = _extract_block(desired)
    old_before, _old_body, old_after = _extract_block(read_text(path))
    if (before, after) != (old_before, old_after):
        raise ValueError("Resource update cannot change content outside the owned block.")
    block = desired[len(before):len(desired) - len(after)] if _BLOCK_BEGIN in desired.splitlines() else None
    digest = hashlib.sha256(json.dumps([before, after], separators=(",", ":")).encode()).hexdigest()
    request = json.dumps({"resource_path": str(path), "outside_digest": digest, "block": block}).encode()
    if len(request) > _MAX_HELPER_BYTES:
        raise ValueError("Protected resource update exceeds the helper request limit.")
    try:
        result = subprocess.run(_HELPER_COMMAND, input=request, capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        raise OSError(HELPER_UNAVAILABLE_MESSAGE) from None
    if result.returncode != 0:
        # The privileged helper intentionally emits no request-dependent details.
        # Keep its rejection actionable without forwarding captured stdout/stderr.
        raise OSError(HELPER_REJECTED_MESSAGE)
    updated = path.stat()
    if path.read_bytes() != contents or (updated.st_uid, updated.st_gid, stat.S_IMODE(updated.st_mode)) != (
        metadata.st_uid, metadata.st_gid, stat.S_IMODE(metadata.st_mode),
    ):
        raise OSError("Protected resource helper did not preserve the requested bytes and metadata.")


def atomic_write(path, contents, metadata=None):
    """Write bytes privately, preserve supplied metadata, then atomically replace."""
    path = Path(path)
    if metadata is not None and os.geteuid() not in (0, metadata.st_uid):
        replace_using_resource_helper(path, contents, metadata)
        return
    fd, name = tempfile.mkstemp(prefix=".pinpoint-resource-", dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(contents)
            stream.flush()
            if metadata is not None:
                current = os.fstat(stream.fileno())
                if (current.st_uid, current.st_gid) != (metadata.st_uid, metadata.st_gid):
                    os.fchown(stream.fileno(), metadata.st_uid, metadata.st_gid)
            os.fchmod(stream.fileno(), stat.S_IMODE(metadata.st_mode) if metadata else _FILE_MODE)
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def write_resource_block(resource_cfg_path, slot_map, values):
    """Atomically replace only the owned block, preserving owner, group and mode."""
    path = Path(resource_cfg_path)
    metadata = path.stat() if path.exists() else None
    if metadata and stat.S_IMODE(metadata.st_mode) & 0o007:
        raise ValueError("Resource file permissions allow other users to read secrets.")
    validate_values(values)
    before, after = _split_around_block(read_text(path))
    reserved = read_reserved_slots(path)
    slots = [_slot_number(macro) for macro in slot_map.values()]
    if len(set(slots)) != len(slots) or set(slots) & reserved:
        raise ValueError("Managed resource macro slot conflicts with another assignment.")
    lines = [_BLOCK_BEGIN + "\n"]
    for key, macro in sorted(slot_map.items(), key=lambda item: _slot_number(item[1])):
        if key not in values:
            raise ValueError("Missing value for managed resource slot.")
        lines.append(f"# PINPOINT KEY {json.dumps(key)} {macro}\n")
        lines.append(f"{macro}={values[key]}\n")
    lines.append(_BLOCK_END + "\n")
    atomic_write(path, (before + "".join(lines) + after).encode(), metadata)


def read_resource_block(resource_cfg_path):
    """Return owned slot values; missing files or absent blocks yield no values."""
    _before, body, _after = _extract_block(read_text(resource_cfg_path))
    result = {}
    for line in body.splitlines():
        match = re.fullmatch(r"\s*(\$USER[0-9]+\$)=(.*)", line)
        if match:
            result[_slot_number(match.group(1))] = match.group(2)
    return result


def reclaim(keys_to_remove, slot_map):
    """Return assignments without the removed keys, leaving the input unchanged."""
    removed = set(keys_to_remove)
    return {key: slot for key, slot in slot_map.items() if key not in removed}


def restore_resource_cfg(backup_path, resource_cfg_path):
    """Restore backup bytes atomically, preserving the destination's ownership."""
    path = Path(resource_cfg_path)
    metadata = path.stat() if path.exists() else Path(backup_path).stat()
    atomic_write(path, Path(backup_path).read_bytes(), metadata)


class ResourceTransaction:
    """Snapshot resource bytes in memory and restore unless application commits.

    Enter before generation while holding the shared config lock. Capturing the
    snapshot must succeed before any writer runs; no secret backup file is left
    on disk. A rollback failure raises rather than reporting a safe apply.
    """

    def __init__(self, path):
        self.path = Path(path)
        self.metadata = None
        self.contents = None
        self.committed = False

    def __enter__(self):
        if self.path.exists():
            self.metadata = self.path.stat()
            self.contents = self.path.read_bytes()
        return self

    def changed(self):
        """True when resource bytes differ from the pre-generation snapshot."""
        try:
            contents = self.path.read_bytes()
        except FileNotFoundError:
            contents = None
        return contents != self.contents

    def rollback(self):
        """Restore original bytes and metadata before a rollback daemon reload."""
        if not self.changed():
            return
        if self.contents is None:
            self.path.unlink(missing_ok=True)
        else:
            atomic_write(self.path, self.contents, self.metadata)

    def commit(self):
        """Retain the new resource only once validation and application succeed."""
        self.committed = True

    def __exit__(self, exc_type, exc, traceback):
        try:
            if not self.committed:
                self.rollback()
        finally:
            self.contents = None
