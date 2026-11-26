# Contributing

Pinpoint is licensed under the GNU General Public License v3.0 (provisional;
see [`docs/Hand_Off.md`](docs/Hand_Off.md#license)). By contributing you agree
your changes are offered under the same terms. Credits are in [`NOTICE`](NOTICE).

Before you open a pull request, run everything CI runs:

```bash
scripts/verify.sh all
```

The three blocking CI jobs are `docs`, `backend` and `frontend`; what each one
checks, and what to do when one fails, is in
[`spec files/Agent_Workflow_and_CI.md`](spec%20files/Agent_Workflow_and_CI.md).

Read the [specification index](spec%20files/README.md) before changing system
behavior, keep the matching specification current, and never commit credentials,
private keys, database backups or unsanitized test evidence.
