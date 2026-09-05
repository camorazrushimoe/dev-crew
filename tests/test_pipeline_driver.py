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


class TestDecide(unittest.TestCase):
    def test_fresh_pr_dispatches_reviews(self):
        self.assertEqual(decide(1, "BON-85: x", [], {}), [("reviews", 1, "BON-85: x")])

    def test_reviews_dispatched_waits(self):
        state = {"1": {"reviews_dispatched": True}}
        self.assertEqual(decide(1, "x", [], state), [])

    def test_partial_review_waits(self):
        comments = ["## QA Report — **Verdict: approve**"]
        state = {"1": {"reviews_dispatched": True}}
        self.assertEqual(decide(1, "x", comments, state), [])

    def test_both_approve_merges(self):
        comments = [
            "## QA Report — **Verdict: approve**",
            "## Tech PM review — **Verdict: approve**",
        ]
        self.assertEqual(decide(1, "x", comments, {}), [("merge", 1, "x")])

    def test_needs_changes_fixes(self):
        comments = ["## QA Report — **Verdict: needs-changes**"]
        self.assertEqual(decide(1, "x", comments, {}), [("fix", 1, "x")])

    def test_fix_not_redispatched(self):
        comments = ["## QA Report — **Verdict: needs-changes**"]
        state = {"1": {"fix_dispatched": True}}
        self.assertEqual(decide(1, "x", comments, state), [])

    def test_fix_takes_priority_over_approve(self):
        # qa approves but tech-pm still needs-changes -> fix, not merge.
        comments = [
            "## QA Report — **Verdict: approve**",
            "## Tech PM review — **Verdict: needs-changes**",
        ]
        self.assertEqual(decide(1, "x", comments, {}), [("fix", 1, "x")])

    def test_merged_is_terminal(self):
        state = {"1": {"merged": True}}
        comments = [
            "## QA Report — **Verdict: approve**",
            "## Tech PM review — **Verdict: approve**",
        ]
        self.assertEqual(decide(1, "x", comments, state), [])


if __name__ == "__main__":
    unittest.main()
