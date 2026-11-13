# `app/ncpa_deployment/` — remote NCPA installation

`ncpa_deployment.py` installs and configures the NCPA agent on a device over
SSH, so Nagios can read its metrics. It checks the device's SSH host-key
fingerprint before it connects, runs commands (with `sudo` where needed),
removes its temporary bootstrap account afterwards, and records the outcome on
the device. It is imported by `app/api/system/ncpa_deployment.py`; it is not run
directly.

Who runs it: an administrator with the NCPA Deployment permission, from the NCPA
Deployment page. It connects to real devices, so tests use fakes.

Operator guide: [NCPA deployment](../../../docs/manuals/NCPA_Deployment.md).
Design and data: [Data Model and Integrations](../../../spec%20files/Data_Model_and_Integrations.md).
