# `client/e2e/` — Playwright browser tests

End-to-end tests that drive a **running** Pinpoint appliance in a browser. They
are separate from the unit tests in `client/src/test/` (Vitest, `npm run test`)
and are never run by `scripts/verify.sh` or CI.

| File | Purpose |
|---|---|
| `*.setup.ts` | Sign-in setup that saves a browser session for the administrator and restricted roles |
| `smoke.*.spec.ts` | Basic page smokes for the administrator and a restricted user |
| `*.lab.spec.ts` | Feature checks that need a lab: notification policy, escalations, email settings, device identity, DHCP history, host recipients, storage logs, and so on |
| `qa-*.lab.spec.ts` | Source adapters for the black-box QA cases; selected by [`../qa/`](../qa/README.md) |
| `labAddresses.ts` | The lab address prefixes the tests are allowed to act on |

Who runs it: a tester or agent against a disposable lab (the
[local Docker lab](../../docs/manuals/Local_Lab.md) or the VM lab), through
[`scripts/playwright-lab`](../../scripts/README.md) so credentials stay out of
the repository. Configs are `client/playwright*.config.ts`. Never point these at
a production server: the lab specs change settings and can stop services.
