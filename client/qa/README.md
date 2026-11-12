# `client/qa/` — QA case selection for the browser tests

Small ES modules that decide which black-box QA cases a Playwright run may
execute and where its evidence goes. They run no browser and touch no lab.

| File | Does |
|---|---|
| `selection.mjs` | Exact case selection and private, non-overwriting evidence paths for the permission cases; used by `playwright.qa.config.ts` |
| `module-selection.mjs` | The same for the Modules 2–9 cases; used by `playwright.modules.qa.config.ts` |
| `*.node.mjs` | Node unit tests for the selectors and timing (`node --test client/qa/*.node.mjs`) |

Who runs it: the QA tooling in [`scripts/`](../../scripts/README.md)
(`qa_pilot.py`, `qa_execute.py`) supplies the environment; people normally do
not run these directly. The cases are defined in the
[black-box catalog](../../docs/qa/Pinpoint%20-%20Black-Box%20Test%20Cases%20by%20Module%20with%20Traceability%20Matrix.md);
background in [Automation readiness](../../docs/qa/Automation_Readiness.md).
