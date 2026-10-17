"""
Code-defined remediation action types.

An admin picks a type from this registry and fills in its parameters; nothing an admin or a
Nagios event supplies is ever used as a command, script path or unit name. Each type has a
parameter schema, a ``validate`` that returns cleaned values and one error per bad field,
and a ``run`` that takes the validated parameters and a RunContext.

Shipped here: ``record_only`` (changes nothing), ``restart_local_service`` (restarts one
unit from a fixed list on the PinPoint host) and ``restart_remote_service`` (restarts one unit
from a per-device list on a trusted monitored device over SSH). More recovery types are added to ACTION_TYPES
through this same registry.
"""
import subprocess
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass
from typing import Any, Callable, Optional

DEFAULT_TIMEOUT_SECONDS = 30
MAX_OUTPUT_CHARS = 1024

# Units ``restart_local_service`` may restart. The installer sudoers drop-in must list exactly
# these units (one full command line each, no wildcard); change both together. pinpoint-gunicorn
# is left out on purpose: restarting it would kill the process that runs the restart.
RESTARTABLE_UNITS = ("nagios",)
SYSTEMCTL_PATH = "/usr/bin/systemctl"
RESTART_SUBPROCESS_TIMEOUT_SECONDS = 20


# ==========================================================
# TYPES
# ==========================================================

@dataclass(frozen=True)
class RemoteTarget:
    """A trusted device a remote action may act on, read by the consumer before the action runs."""
    ip_address: str
    ssh_port: int
    fingerprint: str
    services: tuple


@dataclass(frozen=True)
class RunContext:
    """What an action may know about the event: names and state only, never raw spool text."""
    hostname: str
    service: Optional[str]
    state: str
    # Read by the consumer before the action runs, because the action runs in a worker thread
    # without an application context.
    maintenance_mode: bool = False
    # Set for remote actions only. ``remote_target`` is None when the device may not be acted on,
    # and ``remote_refusal`` then says why in fixed text. ``app`` lets the action open an
    # application context in its worker thread (the SSH helpers log through current_app).
    remote_target: Optional[RemoteTarget] = None
    remote_refusal: Optional[str] = None
    app: Any = None


class ActionFailed(Exception):
    """Raised by an action with a short fixed message that is safe to record (no raw exception text)."""


class ActionTimedOut(Exception):
    """Raised by an action whose own command overran; the message is recorded as the output."""


@dataclass(frozen=True)
class RunResult:
    """Outcome is one of succeeded, failed, timed_out; output is short and never a raw exception."""
    outcome: str
    output: str


@dataclass(frozen=True)
class ActionType:
    key: str
    label: str
    description: str
    parameters: list
    validate: Callable[[Any], tuple]
    run: Callable[[dict, RunContext], str]
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS


# ==========================================================
# record_only
# ==========================================================

def validate_no_parameters(params):
    """Accept only an empty object; every key is reported against its own field. Returns (cleaned, errors)."""
    if params is None:
        return {}, {}
    if not isinstance(params, dict):
        return {}, {"parameters": "Parameters must be an object."}
    errors = {key: "This action takes no parameters." for key in params}
    return {}, errors


def run_record_only(params, context):
    """Change nothing; the run row written by the consumer is the whole effect."""
    return "recorded"


# ==========================================================
# restart_local_service
# ==========================================================

def validate_restart_local_service(params):
    """Accept only {"unit": <one of RESTARTABLE_UNITS>}. Returns (cleaned, errors)."""
    if params is None:
        params = {}
    if not isinstance(params, dict):
        return {}, {"parameters": "Parameters must be an object."}
    errors = {key: "This action does not take this parameter." for key in params if key != "unit"}
    unit = params.get("unit")
    if not isinstance(unit, str) or unit not in RESTARTABLE_UNITS:
        errors["unit"] = "Choose one of: " + ", ".join(RESTARTABLE_UNITS) + "."
    if errors:
        return {}, errors
    return {"unit": unit}, {}


def run_restart_local_service(params, context):
    """
    Restart one listed unit with ``sudo -n systemctl restart <unit>`` (argument list, no shell).
    Refused in Maintenance Mode or for a unit off the list. Only the exit code is recorded;
    the command's own output is never kept.
    """
    unit = params.get("unit")
    if unit not in RESTARTABLE_UNITS:
        raise ActionFailed("Refused: that service is not on the list of services PinPoint may restart.")
    if context.maintenance_mode:
        raise ActionFailed("Refused: Maintenance Mode is on.")
    try:
        done = subprocess.run(
            ["sudo", "-n", SYSTEMCTL_PATH, "restart", unit],
            capture_output=True, text=True, timeout=RESTART_SUBPROCESS_TIMEOUT_SECONDS, check=False)
    except subprocess.TimeoutExpired:
        raise ActionTimedOut(f"Restarting {unit} did not finish in time.")
    except OSError:
        raise ActionFailed("Could not run sudo on this host.")
    if done.returncode != 0:
        raise ActionFailed(f"Restart of {unit} failed with exit code {done.returncode}.")
    return f"Restarted {unit}; exit code 0."


# ==========================================================
# restart_remote_service
# ==========================================================

def validate_restart_remote_service(params):
    """
    Accept only {"unit": <plain unit name>}. Which units a device really allows is checked at run
    time against that device's own list, so only the name's shape is checked here.
    Returns (cleaned, errors).
    """
    from app.remote_restart import valid_unit
    if params is None:
        params = {}
    if not isinstance(params, dict):
        return {}, {"parameters": "Parameters must be an object."}
    errors = {key: "This action does not take this parameter." for key in params if key != "unit"}
    unit = params.get("unit")
    if not valid_unit(unit):
        errors["unit"] = "Enter a plain service name such as nagios or apache2."
    if errors:
        return {}, errors
    return {"unit": unit}, {}


def run_restart_remote_service(params, context):
    """
    Restart one unit on the device the event came from, over SSH with the deployment key.
    Refused in Maintenance Mode, for a device that is not active, trusted and enabled, and for a
    unit not on that device's list. A changed host key stops the run. Only fixed text is recorded.
    """
    from app.remote_restart import restart_remote_unit, valid_unit
    unit = params.get("unit")
    if not valid_unit(unit):
        raise ActionFailed("Refused: that is not a valid service name.")
    if context.maintenance_mode:
        raise ActionFailed("Refused: Maintenance Mode is on.")
    target = context.remote_target
    if target is None:
        raise ActionFailed(context.remote_refusal or "Refused: this device cannot be restarted remotely.")
    if unit not in target.services:
        raise ActionFailed("Refused: that service is not on this device's restart list.")
    if context.app is None:
        raise ActionFailed("Refused: no application context for the remote restart.")
    with context.app.app_context():
        outcome, message = restart_remote_unit(target.ip_address, target.ssh_port, target.fingerprint, unit)
    if outcome == "succeeded":
        return message
    if outcome == "timed_out":
        raise ActionTimedOut(message)
    raise ActionFailed(message)


ACTION_TYPES = {
    "record_only": ActionType(
        key="record_only",
        label="Record only",
        description="Changes nothing. Writes a line in the run log each time the rule matches, "
                    "so you can see what a rule would cover before a real action is attached.",
        parameters=[],
        validate=validate_no_parameters,
        run=run_record_only,
    ),
    "restart_local_service": ActionType(
        key="restart_local_service",
        label="Restart a PinPoint host service",
        description="Restarts one service on the PinPoint host itself (for example Nagios) when a covered "
                    "check fails. Only the listed services can be chosen. Not run in Maintenance Mode.",
        parameters=[{
            "name": "unit", "label": "Service to restart", "type": "choice",
            "choices": list(RESTARTABLE_UNITS), "required": True,
        }],
        validate=validate_restart_local_service,
        run=run_restart_local_service,
    ),
    "restart_remote_service": ActionType(
        key="restart_remote_service",
        label="Restart a service on the monitored device",
        description="Restarts one service on the device where a check failed, over SSH, when the device is "
                    "active, not paused, trusted and has remote restart turned on, and the service is on "
                    "that device's list. A changed SSH host key stops it. Not run in Maintenance Mode.",
        parameters=[{
            "name": "unit", "label": "Service to restart", "type": "text", "required": True,
        }],
        validate=validate_restart_remote_service,
        run=run_restart_remote_service,
    ),
}


# ==========================================================
# PUBLIC HELPERS
# ==========================================================

def describe_types():
    """Return each type as a plain dict (key, label, description, parameters) for the form."""
    return [
        {"key": t.key, "label": t.label, "description": t.description, "parameters": list(t.parameters)}
        for t in ACTION_TYPES.values()
    ]


def validate_parameters(action_type, params):
    """Validate params for a type. Returns (cleaned, errors); errors maps a field name to a message."""
    registered = ACTION_TYPES.get(action_type)
    if registered is None:
        return {}, {"actionType": "Unknown action type."}
    return registered.validate(params)


def run_action(action_type, params, context):
    """
    Run one action with its timeout and return a RunResult. Never raises: an unknown type, a
    crash or a timeout becomes a failed or timed_out result with a fixed message, so a secret in
    an exception text cannot reach the run log.
    """
    registered = ACTION_TYPES.get(action_type)
    if registered is None:
        return RunResult("failed", "Unknown action type.")
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        future = pool.submit(registered.run, params, context)
        try:
            output = future.result(timeout=registered.timeout_seconds)
        except FutureTimeout:
            return RunResult("timed_out", "The action did not finish in time.")
        except ActionTimedOut as error:
            return RunResult("timed_out", str(error))
        except ActionFailed as error:
            return RunResult("failed", str(error))
        except Exception:
            return RunResult("failed", "The action failed.")
        return RunResult("succeeded", str(output)[:MAX_OUTPUT_CHARS])
    finally:
        pool.shutdown(wait=False)
