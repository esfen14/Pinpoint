"""Contract checks for the documented fix-found queue and stop rules."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = (ROOT / ".agent/workflows/fix-found.md").read_text()
WORK_ISSUE = (ROOT / ".agent/workflows/work-issue.md").read_text()
QA_RUN = (ROOT / ".agent/workflows/qa-run.md").read_text()


class FixFoundContract(unittest.TestCase):
    def test_uses_issue_scoped_progress_and_delegates_work(self):
        self.assertIn(".agent/progress/issue-<tracking-number>.md", WORKFLOW)
        self.assertIn("Follow `work-issue.md` exactly", WORKFLOW)
        self.assertIn("issue-NUMBER-*", WORKFLOW)

    def test_queue_fetches_all_pages_and_filters_pull_requests(self):
        self.assertIn("gh api --paginate", WORKFLOW)
        self.assertIn("labels=qa-found", WORKFLOW)
        self.assertIn("select(.pull_request == null)", WORKFLOW)
        self.assertIn("created_at", WORKFLOW)
        self.assertIn("severity descending", WORKFLOW)

    def test_skip_rules_are_explicit(self):
        for rule in (
            "has `needs-decision`",
            "has an open fix PR",
            "has no valid case ID",
            "touches a sensitive module",
            "belongs to the installer",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, WORKFLOW)

    def test_limits_and_permission_stop_are_explicit(self):
        for rule in (
            "At most three PRs",
            "two merged fixes",
            "If any permission is denied",
            "Never merge",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, WORKFLOW)

    def test_retest_requires_a_real_merged_fix(self):
        for rule in (
            "gh pr view PR_NUMBER --json state,mergedAt,mergeCommit,body,url",
            "gh pr diff PR_NUMBER",
            "Only after the fix is merged and the finding closed",
            "documentation PR alone is not proof of a product fix",
            "record affected current case",
            "eligibility as `retest required`",
            "do not overwrite human verdicts",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, WORKFLOW)

    def test_work_issue_keeps_human_merge_gate(self):
        self.assertIn("Never merge a pull request", WORK_ISSUE)

    def test_planted_harness_failure_is_not_a_product_issue(self):
        self.assertIn("deliberately false scratch assertion", QA_RUN)
        self.assertIn("not create a `qa-found`", QA_RUN)
        self.assertIn("do not create a `qa-found`", QA_RUN)

    def test_qa_run_syncs_every_result_artifact_before_checkpointing(self):
        for requirement in (
            "docs/qa/QA_Case_Status.md",
            "queue's execution log",
            "render_qa_case_tables.py --write",
            "scripts/verify.sh docs",
            "before checkpointing",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, QA_RUN)

    def test_completed_qa_run_closes_its_tracking_issue_through_the_pr(self):
        for requirement in (
            "every master-plan case",
            "Closes #<n>",
            "closes the tracking issue when the PR merges",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, QA_RUN)


if __name__ == "__main__":
    unittest.main()
