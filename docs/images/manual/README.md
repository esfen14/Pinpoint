# Manual screenshots

Real screenshots of Pinpoint for the [User Manual](../../User_Manual/User_Manual.md) and the guides in [`docs/manuals/`](../../manuals/README.md). Light theme, 1440x900.

Regenerate against a disposable demo lab (build it with [`Demo_Lab_QA_Handoff.md`](../../qa/Demo_Lab_QA_Handoff.md), with a critical and an acknowledged alert and a device with ports):

```bash
scripts/playwright-lab --project=manual-screenshots
```

The spec is [`client/e2e/manual-screenshots.lab.spec.ts`](../../../client/e2e/manual-screenshots.lab.spec.ts). It only navigates and screenshots. Check every image for credentials or off-lab addresses before committing.
