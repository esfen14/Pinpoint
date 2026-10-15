"""
Code-defined remediation action types.

An admin picks a type from this registry and fills in its parameters; nothing an admin or a
Nagios event supplies is ever used as a command, script path or unit name. Each type has a
parameter schema, a ``validate`` that returns cleaned values and one error per bad field,
and a ``run`` that takes the validated parameters and a RunContext.

Shipped here: ``record_only`` (changes nothing). Real recovery types are added to
ACTION_TYPES by later issues through this same registry.
"""
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass
from typing import Any, Callable, Optional

DEFAULT_TIMEOUT_SECONDS = 30
MAX_OUTPUT_CHARS = 1024


# ==========================================================
# TYPES
# ==========================================================

@dataclass(frozen=True)
class RunContext:
    """What an action may know about the event: names and state only, never raw spool text."""
    hostname: str
    service: Optional[str]
    state: str


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
        except Exception:
            return RunResult("failed", "The action failed.")
        return RunResult("succeeded", str(output)[:MAX_OUTPUT_CHARS])
    finally:
        pool.shutdown(wait=False)
