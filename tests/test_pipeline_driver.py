"""Tests for the deterministic pipeline driver (pure logic only).

Run:  python3 -m unittest tests.test_pipeline_driver -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dashboard"))

from pipeline_driver import parse_verdicts, decide, TICKET_RE  # noqa: E402


class TestTicketBinding(unittest.TestCase):
    def test_dev_crew_pr_title_has_ticket(self):
        self.assertIsNotNone(TICKET_RE.search("BON-84: artworks.ai as live image + video vendor"))
        self.assertIsNotNone(TICKET_RE.search("BON-82: Lichina dance-video §3 — Job + Telegram"))

    def test_owner_pr_title_has_no_ticket(self):
        self.assertIsNone(TICKET_RE.search("spec: identity positioning — same person, different clothes"))
        self.assertIsNone(TICKET_RE.search("spec: ui-polish — static hero art + warmer copy"))
        self.assertIsNone(TICKET_RE.search("docs: продукт — тот же человек, другая одежда"))


class TestParseVerdicts(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(parse_verdicts([]), {"qa": None, "tech-pm": None})

    def test_both_approve(self):
        comments = [
            "## QA Report — **Verdict: approve**",
            "## Tech PM review — verdict: approve",
        ]
        self.assertEqual(
            parse_verdicts(comments), {"qa": "approve", "tech-pm": "approve"}
        )

    def test_needs_changes(self):
        comments = ["## QA Report — **Verdict: needs-changes**"]
        self.assertEqual(parse_verdicts(comments), {"qa": "needs-changes", "tech-pm": None})

    def test_rereview_overwrites_earlier(self):
        comments = [
            "## QA Report — **Verdict: needs-changes**",
            "## QA Report (round 2) — **Verdict: `approve`**",
        ]
        self.assertEqual(parse_verdicts(comments), {"qa": "approve", "tech-pm": None})

    def test_non_review_comment_ignored(self):
        comments = [
            "fixes pushed, no verdict here",
            "## QA Report — **Verdict: approve**",
        ]
        self.assertEqual(parse_verdicts(comments), {"qa": "approve", "tech-pm": None})

    def test_qa_word_without_verdict_ignored(self):
        # 'qa' appears but no 'verdict' keyword -> not a review.
        comments = ["developer notes qa should recheck later"]
        self.assertEqual(parse_verdicts(comments), {"qa": None, "tech-pm": None})

    def test_tech_pm_hyphen_and_space(self):
        comments = [
            "## Tech PM review — verdict: needs-changes",
            "## Tech-PM re-review — verdict: ✅ approve",
        ]
        self.assertEqual(parse_verdicts(comments), {"qa": None, "tech-pm": "approve"})

    def test_ready_to_merge_counts_as_approve(self):
        comments = [
            "## QA Report — **Verdict: approve**",
            "## Tech PM review — **Verdict**: ready to merge, implementation looks solid",
        ]
        self.assertEqual(parse_verdicts(comments), {"qa": "approve", "tech-pm": "approve"})

    def test_lgtm_counts_as_approve(self):
        comments = ["## Tech PM review — lgtm, ship it"]
        self.assertEqual(parse_verdicts(comments), {"qa": None, "tech-pm": "approve"})

    def test_needs_change_without_hyphen(self):
        comments = ["## QA Report — needs change: fix the password default"]
        self.assertEqual(parse_verdicts(comments), {"qa": "needs-changes", "tech-pm": None})

    def test_changes_requested(self):
        comments = ["## Tech PM review — changes requested: scope the gate to new users"]
        self.assertEqual(parse_verdicts(comments), {"qa": None, "tech-pm": "needs-changes"})

    def test_pm_manager_header_counts_as_pm(self):
        # PM uses "manager/spec-conformance review" header and mentions QA in body.
        comments = [
            "## BON-86 · Slice 1 — access-gate: manager/spec-conformance RE-REVIEW\n"
            "QA already approved twice; this adds the manager lens.\n"
            "**Verdict: approve — 0 blockers.**",
        ]
        self.assertEqual(parse_verdicts(comments), {"qa": None, "tech-pm": "approve"})

    def test_qa_mentioning_manager_stays_qa(self):
        # QA header, but the body mentions "manager finding".
        comments = [
            "## QA Report — re-review\n"
            "Remaining unchecked §0 left for post-merge, per the manager finding.\n"
            "**Verdict: approve**",
        ]
        self.assertEqual(parse_verdicts(comments), {"qa": "approve", "tech-pm": None})


class TestDecide(unittest.TestCase):
    H0 = "aaaa0000"
    H1 = "bbbb1111"

    def test_fresh_pr_dispatches_reviews(self):
        self.assertEqual(decide(1, "BON-85: x", self.H0, [], {}), [("reviews", 1, "BON-85: x")])

    def test_reviews_dispatched_waits(self):
        state = {"1": {"stage": "review", "head": self.H0}}
        self.assertEqual(decide(1, "x", self.H0, [], state), [])

    def test_partial_review_waits(self):
        comments = ["## QA Report — **Verdict: approve**"]
        state = {"1": {"stage": "review", "head": self.H0}}
        self.assertEqual(decide(1, "x", self.H0, comments, state), [])

    def test_both_approve_merges(self):
        comments = [
            "## QA Report — **Verdict: approve**",
            "## Tech PM review — **Verdict: approve**",
        ]
        self.assertEqual(decide(1, "x", self.H0, comments, {}), [("merge", 1, "x")])

    def test_needs_changes_fixes(self):
        comments = ["## QA Report — **Verdict: needs-changes**"]
        self.assertEqual(decide(1, "x", self.H0, comments, {}), [("fix", 1, "x")])

    def test_fix_waiting_for_push_does_not_redispatch(self):
        comments = ["## QA Report — **Verdict: needs-changes**"]
        state = {"1": {"stage": "fix", "head": self.H0}}
        self.assertEqual(decide(1, "x", self.H0, comments, state), [])

    def test_fix_then_head_change_triggers_rereview(self):
        comments = ["## QA Report — **Verdict: needs-changes**"]
        state = {"1": {"stage": "fix", "head": self.H0}}
        self.assertEqual(decide(1, "x", self.H1, comments, state), [("re-review", 1, "x")])

    def test_rereview_waiting_does_not_refix(self):
        comments = ["## QA Report — **Verdict: needs-changes**"]
        state = {"1": {"stage": "re-review", "head": self.H1}}
        self.assertEqual(decide(1, "x", self.H1, comments, state), [])

    def test_fix_takes_priority_over_approve(self):
        # qa approves but tech-pm still needs-changes -> fix, not merge.
        comments = [
            "## QA Report — **Verdict: approve**",
            "## Tech PM review — **Verdict: needs-changes**",
        ]
        self.assertEqual(decide(1, "x", self.H0, comments, {}), [("fix", 1, "x")])

    def test_merged_is_terminal(self):
        state = {"1": {"merged": True}}
        comments = [
            "## QA Report — **Verdict: approve**",
            "## Tech PM review — **Verdict: approve**",
        ]
        self.assertEqual(decide(1, "x", self.H0, comments, state), [])


if __name__ == "__main__":
    unittest.main()
