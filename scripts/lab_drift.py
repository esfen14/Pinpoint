"""Compare the versions pinned in lab/appliance/Dockerfile with the PinPoint-Installer.

    python3 -I scripts/lab_drift.py --installer-dir <PinPoint-Installer checkout>

Run through `scripts/lab check-drift`, which finds the installer checkout. The
installer side is read from its newest baseline manifest
(setup/manifests/pp-mon-baseline-<n>.json) and setup/deploy-pinpoint-web.sh.

Exit status: 0 the pins match, 1 at least one pin differs, 2 a file could not
be read. Nothing is downloaded or changed. See docs/manuals/Local_Lab.md.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DOCKERFILE = ROOT / 'lab' / 'appliance' / 'Dockerfile'

# Pin name, then the label shown in the report. The order is the report order.
PINS = [
    ('ubuntu', 'Ubuntu release'),
    ('nagios_version', 'Nagios Core version'),
    ('nagios_url', 'Nagios Core download URL'),
    ('nagios_sha256', 'Nagios Core SHA-256'),
    ('plugins_version', 'Nagios Plugins version'),
    ('plugins_url', 'Nagios Plugins download URL'),
    ('plugins_sha256', 'Nagios Plugins SHA-256'),
    ('ncpa_url', 'check_ncpa download URL'),
    ('ncpa_sha256', 'check_ncpa SHA-256'),
    ('python_version', 'Python version'),
    ('gunicorn', 'Gunicorn requirement'),
]
PIN_NAMES = []
for _name, _label in PINS:
    PIN_NAMES.append(_name)

# Dockerfile ARG name for each pin that is a plain build argument.
DOCKERFILE_ARGS = {
    'nagios_version': 'NAGIOS_VERSION',
    'nagios_sha256': 'NAGIOS_SHA256',
    'plugins_version': 'PLUGINS_VERSION',
    'plugins_sha256': 'PLUGINS_SHA256',
    'ncpa_sha256': 'NCPA_SHA256',
    'python_version': 'PYTHON_VERSION',
}
# A word that identifies each download URL in the Dockerfile.
URL_MARKERS = {
    'nagios_url': '/nagioscore/',
    'plugins_url': 'nagios-plugins',
    'ncpa_url': 'check_ncpa',
}
BASELINE_NAME = re.compile(r'pp-mon-baseline-(\d+)\.json$')


class DriftError(Exception):
    """A file needed for the comparison is missing or not in the expected form."""


def empty_pins():
    pins = {}
    for name in PIN_NAMES:
        pins[name] = None
    return pins


def substitute_arguments(text, arguments):
    """Replace ${NAME} and $NAME with the Dockerfile's ARG defaults."""
    def replace(match):
        name = match.group(1) or match.group(2)
        return arguments.get(name, match.group(0))
    return re.sub(r'\$\{(\w+)\}|\$(\w+)', replace, text)


def dockerfile_pins(text):
    """Return the pins found in the Dockerfile text; a missing pin is None."""
    pins = empty_pins()
    arguments = {}
    for match in re.finditer(r'^ARG\s+(\w+)=(\S+)\s*$', text, re.M):
        arguments[match.group(1)] = match.group(2)
    for name, argument in DOCKERFILE_ARGS.items():
        pins[name] = arguments.get(argument)

    base = re.search(r'^FROM\s+ubuntu:(\S+)', text, re.M)
    if base:
        pins['ubuntu'] = base.group(1)

    for match in re.finditer(r'\bwget\b[^\n]*?(https?://\S+)', text):
        url = substitute_arguments(match.group(1), arguments)
        for name, marker in URL_MARKERS.items():
            if marker in url and pins[name] is None:
                pins[name] = url

    gunicorn = re.search(r'"(gunicorn[^"\s]*)"', text)
    if gunicorn:
        pins['gunicorn'] = gunicorn.group(1)
    return pins


def baseline_manifest(installer_dir):
    """Return the path of the highest-numbered baseline manifest."""
    folder = Path(installer_dir) / 'setup' / 'manifests'
    best_number = -1
    best_path = None
    if folder.is_dir():
        for path in folder.iterdir():
            match = BASELINE_NAME.match(path.name)
            if match and int(match.group(1)) > best_number:
                best_number = int(match.group(1))
                best_path = path
    if best_path is None:
        raise DriftError('no baseline manifest (pp-mon-baseline-<n>.json) in %s; '
                         'is the installer checkout up to date?' % folder)
    return best_path


def shell_value(text, name):
    """Return the value of a NAME="value" assignment in a shell script, or None."""
    match = re.search(r'^%s=(["\']?)([^"\'\n]*)\1\s*$' % re.escape(name), text, re.M)
    if match:
        return match.group(2)
    return None


def installer_pins(installer_dir):
    """Return the pins the installer checkout defines; a missing pin is None."""
    manifest_path = baseline_manifest(installer_dir)
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise DriftError('cannot read manifest %s: %s' % (manifest_path, error))
    if not isinstance(manifest, dict):
        raise DriftError('manifest %s is not a JSON object' % manifest_path)

    pins = empty_pins()
    platform = manifest.get('platform') or {}
    if platform.get('os') == 'ubuntu':
        pins['ubuntu'] = platform.get('version')

    components = manifest.get('components') or {}
    for prefix, component_name in (('nagios', 'nagios-core'), ('plugins', 'nagios-plugins'),
                                   ('ncpa', 'check-ncpa')):
        component = components.get(component_name) or {}
        artifact = component.get('artifact') or {}
        if prefix + '_version' in pins:
            pins[prefix + '_version'] = component.get('version')
        pins[prefix + '_url'] = artifact.get('url')
        pins[prefix + '_sha256'] = artifact.get('sha256')

    deploy_path = Path(installer_dir) / 'setup' / 'deploy-pinpoint-web.sh'
    try:
        deploy = deploy_path.read_text(encoding='utf-8')
    except OSError as error:
        raise DriftError('cannot read %s: %s' % (deploy_path, error))
    pins['python_version'] = shell_value(deploy, 'PYTHON_VERSION')
    pins['gunicorn'] = shell_value(deploy, 'GUNICORN_REQUIREMENT')
    return pins


def compare(lab, installer):
    """Return (name, lab value, installer value) for each pin that differs or is missing."""
    differences = []
    for name in PIN_NAMES:
        lab_value = lab.get(name)
        installer_value = installer.get(name)
        if lab_value is None or installer_value is None or lab_value != installer_value:
            differences.append((name, lab_value, installer_value))
    return differences


def shown(value):
    if value is None:
        return '(not found)'
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description='Compare lab/appliance/Dockerfile pins with the installer.')
    parser.add_argument('--installer-dir', required=True, help='a PinPoint-Installer checkout')
    parser.add_argument('--dockerfile', default=str(DEFAULT_DOCKERFILE))
    parser.add_argument('--installer-label', default='', help='text shown for the installer revision')
    options = parser.parse_args(argv)

    try:
        try:
            dockerfile_text = Path(options.dockerfile).read_text(encoding='utf-8')
        except OSError as error:
            raise DriftError('cannot read %s: %s' % (options.dockerfile, error))
        lab = dockerfile_pins(dockerfile_text)
        manifest_name = baseline_manifest(options.installer_dir).stem
        installer = installer_pins(options.installer_dir)
    except DriftError as error:
        print('lab drift: %s' % error, file=sys.stderr)
        return 2

    source = '%s, manifest %s' % (options.installer_dir, manifest_name)
    if options.installer_label:
        source = '%s at %s' % (source, options.installer_label)
    differences = compare(lab, installer)
    if not differences:
        print('lab drift: %d pins match the installer (%s)' % (len(PIN_NAMES), source))
        return 0

    labels = dict(PINS)
    print('lab drift: %d of %d pins differ from the installer (%s)'
          % (len(differences), len(PIN_NAMES), source), file=sys.stderr)
    for name, lab_value, installer_value in differences:
        print('  %s' % labels[name], file=sys.stderr)
        print('    lab/appliance/Dockerfile: %s' % shown(lab_value), file=sys.stderr)
        print('    installer:                %s' % shown(installer_value), file=sys.stderr)
    print('Update lab/appliance/Dockerfile (and re-audit, see docs/manuals/Local_Lab.md).', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
