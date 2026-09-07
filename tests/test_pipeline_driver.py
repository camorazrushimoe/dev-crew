"""Tests for the deterministic pipeline driver (pure logic only).

Run:  python3 -m unittest tests.test_pipeline_driver -v
"""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dashboard"))

import pipeline_driver as pd  # noqa: E402
from pipeline_driver import (  # noqa: E402
    parse_verdicts,
    decide,
    TICKET_RE,
    needs_human_comment,
)


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

    def test_pm_round_review_title_counts_as_pm(self):
        # PM round-3/4 titles dropped "manager": "round-N re-review at head …".
        comments = [
            "## BON-86 · Slice 2 — twerk-video: round-4 re-review at head f63734d (B2 fix)\n"
            "**Verdict: approve — 0 blockers.**",
        ]
        self.assertEqual(parse_verdicts(comments), {"qa": None, "tech-pm": "approve"})

    def test_strict_qa_header(self):
        comments = ["## QA Review\n**Verdict: approve**"]
        self.assertEqual(parse_verdicts(comments), {"qa": "approve", "tech-pm": None})

    def test_strict_pm_header(self):
        comments = ["## Tech PM Review\n**Verdict: approve**"]
        self.assertEqual(parse_verdicts(comments), {"qa": None, "tech-pm": "approve"})

    def test_verdict_anchor_ignores_prior_round_mention(self):
        # Actual verdict "approve"; body mentions a prior round's "needs-changes".
        comments = [
            "## Tech PM Review\n"
            "**Verdict: approve — 0 blockers.**\n"
            "Round-3 blocker B2 resolved; QA's round-3 verdict was `needs-changes`.",
        ]
        self.assertEqual(parse_verdicts(comments), {"qa": None, "tech-pm": "approve"})


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


class TestLoopBreaker(unittest.TestCase):
    """Review-cycle loop breaker (#35): rounds cap, re-review advance, needs-human.

    Acceptance list mirrors openspec/changes/review-cycle-loop-breaker/design.md
    D8 and the spec delta scenarios. ``DRIVER_MAX_REVIEW_ROUNDS`` is a module
    global (env-derived at import); tests patch it directly.
    """

    H0 = "aaaa0000"
    H1 = "bbbb1111"
    H2 = "cccc3333"
    T = "BON-84: artworks"

    def setUp(self):
        self._saved_cap = getattr(pd, "DRIVER_MAX_REVIEW_ROUNDS", 2)

    def tearDown(self):
        pd.DRIVER_MAX_REVIEW_ROUNDS = self._saved_cap

    @staticmethod
    def _qa(round_no, verdict="needs-changes"):
        return f"## QA Report (round {round_no}) — **Verdict: {verdict}**"

    @staticmethod
    def _pm(round_no, verdict="needs-changes"):
        return f"## Tech PM review (round {round_no}) — **Verdict: {verdict}**"

    def test_third_needs_changes_escalates_at_default_cap(self):
        # Two completed rounds; a third needs-changes on the re-reviewed head
        # must escalate (default cap 2) instead of dispatching another fix.
        state = {"1": {"stage": "re-review", "head": self.H2, "rounds": 2,
                       "qa_verdicts": 2, "pm_verdicts": 0}}
        comments = [self._qa(1), self._qa(2), self._qa(3)]
        self.assertEqual(
            decide(1, self.T, self.H2, comments, state),
            [("needs-human", 1, self.T)],
        )

    def test_cap_one_second_needs_changes_escalates(self):
        pd.DRIVER_MAX_REVIEW_ROUNDS = 1
        state = {"1": {"stage": "re-review", "head": self.H1, "rounds": 1,
                       "qa_verdicts": 1, "pm_verdicts": 0}}
        comments = [self._qa(1), self._qa(2)]
        self.assertEqual(
            decide(1, self.T, self.H1, comments, state),
            [("needs-human", 1, self.T)],
        )

    def test_cap_one_first_fix_still_dispatched(self):
        pd.DRIVER_MAX_REVIEW_ROUNDS = 1
        self.assertEqual(
            decide(1, self.T, self.H0, [self._qa(1)], {}),
            [("fix", 1, self.T)],
        )

    def test_both_reviewers_needs_changes_same_head_one_fix(self):
        comments = [self._qa(1), self._pm(1)]
        self.assertEqual(decide(1, self.T, self.H0, comments, {}),
                         [("fix", 1, self.T)])

    def test_needs_human_terminal_suppresses_all_actions(self):
        state = {"1": {"stage": "re-review", "head": self.H0, "rounds": 2,
                       "needs_human": True,
                       "needs_human_at": "2026-09-07T12:00:00Z",
                       "reason": "review-cycle cap reached"}}
        approve = [
            "## QA Review — **Verdict: approve**",
            "## Tech PM review — **Verdict: approve**",
        ]
        # New head commits AND approve verdicts: still suppressed.
        self.assertEqual(decide(1, self.T, "ffff9999", approve, state), [])
        # New needs-changes verdict: still suppressed.
        self.assertEqual(decide(1, self.T, "ffff9999",
                                [self._qa(1)], state), [])

    def test_human_reset_resumes_driver(self):
        # needs_human cleared (human reset out-of-band) -> rules apply again.
        state = {"1": {"stage": "review", "head": self.H0,
                       "needs_human": False}}
        approve = [
            "## QA Review — **Verdict: approve**",
            "## Tech PM review — **Verdict: approve**",
        ]
        self.assertEqual(decide(1, self.T, self.H0, approve, state),
                         [("merge", 1, self.T)])

    def test_needs_human_comment_is_neutral_to_parser(self):
        body = needs_human_comment(7, self.T, 2)
        self.assertEqual(parse_verdicts([body]),
                         {"qa": None, "tech-pm": None})

    def test_driver_own_comment_ignored_even_with_verdict_lexemes(self):
        # Sentinel short-circuit: even a hostile driver comment that contains
        # reviewer/verdict lexemes must not flip parsed verdicts.
        hostile = ("<!-- conveyor:needs-human -->\n"
                   "## Loop breaker\n"
                   "**Verdict: needs-changes** approve lgtm changes requested")
        self.assertEqual(parse_verdicts([hostile]),
                         {"qa": None, "tech-pm": None})
        comments = [hostile, self._qa(1, "approve")]
        self.assertEqual(parse_verdicts(comments),
                         {"qa": "approve", "tech-pm": None})

    def test_legacy_state_without_new_keys(self):
        # No rounds key -> treated as 0 (fix still allowed under the cap).
        self.assertEqual(
            decide(1, self.T, self.H0, [self._qa(1)],
                   {"1": {"stage": "review", "head": self.H0}}),
            [("fix", 1, self.T)],
        )
        # Legacy re-review entry (no verdict counters) -> the needs-changes on
        # record is treated as already accounted for (wait, not re-fix).
        self.assertEqual(
            decide(1, self.T, self.H1, [self._qa(1)],
                   {"1": {"stage": "re-review", "head": self.H1}}),
            [],
        )
        # Legacy fix entry waiting for a push -> no redispatch.
        self.assertEqual(
            decide(1, self.T, self.H0, [self._qa(1)],
                   {"1": {"stage": "fix", "head": self.H0}}),
            [],
        )

    def test_rereview_new_verdict_advances_round(self):
        # QA replied to the re-review with needs-changes (count 2 > recorded 1)
        # -> dispatch the next fix, rounds still below the default cap.
        state = {"1": {"stage": "re-review", "head": self.H1, "rounds": 1,
                       "qa_verdicts": 1, "pm_verdicts": 0}}
        comments = [self._qa(1), self._qa(2)]
        self.assertEqual(decide(1, self.T, self.H1, comments, state),
                         [("fix", 1, self.T)])

    def test_no_double_fix_after_round_advance(self):
        # Round 2 fix was just dispatched on this head; same comments on the
        # same head must not dispatch a second fix.
        state = {"1": {"stage": "fix", "head": self.H1, "rounds": 1,
                       "qa_verdicts": 1, "pm_verdicts": 0}}
        comments = [self._qa(1), self._qa(2)]
        self.assertEqual(decide(1, self.T, self.H1, comments, state), [])


class TestNeedsHumanApply(unittest.TestCase):
    """apply() needs-human action: terminal state + best-effort side effects.

    Review finding (SPEC axis c1): the tech-pm dispatch was unguarded and the
    terminal flags were written after it, so a subprocess failure crashed the
    whole run and left the PR non-terminal — each tick re-decided needs-human
    and re-posted the escalation comment. Spec: side effects SHALL be
    best-effort and SHALL NOT block other PRs; needs-human SHALL be terminal.
    """

    T = "BON-84: artworks"

    def test_apply_posts_comment_and_dispatches_tech_pm(self):
        state = {}
        with mock.patch.object(pd, "post_comment", return_value=(0, "")) as pc, \
             mock.patch.object(pd, "dispatch", return_value=(0, "")) as dsp:
            pd.apply(("needs-human", 1, self.T), state, "aaaa0000", [])
        pc.assert_called_once_with(1, mock.ANY)
        dsp.assert_called_once()
        agent, brief = dsp.call_args.args
        self.assertEqual(agent, "tech-pm")
        self.assertIn("Needs human:", brief)

    def test_apply_marks_terminal_even_if_tech_pm_dispatch_fails(self):
        # A failing tech-pm dispatch must not crash the run (best-effort) and
        # must not leave the PR non-terminal (else the next tick re-decides
        # and re-posts a duplicate escalation comment).
        state = {}
        with mock.patch.object(pd, "post_comment", return_value=(0, "")), \
             mock.patch.object(
                 pd, "dispatch", side_effect=RuntimeError("crew-send.py missing")):
            # Must not raise.
            pd.apply(("needs-human", 1, self.T), state, "aaaa0000", [])
        st = state["1"]
        self.assertTrue(st["needs_human"])
        self.assertIn("needs_human_at", st)
        self.assertIn("review-cycle cap", st["reason"])

    def test_apply_no_tech_pm_dispatch_for_unticketed_pr(self):
        state = {}
        with mock.patch.object(pd, "post_comment", return_value=(0, "")), \
             mock.patch.object(pd, "dispatch", return_value=(0, "")) as dsp:
            pd.apply(("needs-human", 1, "docs: housekeeping"), state,
                     "aaaa0000", [])
        dsp.assert_not_called()

    def test_needs_human_comment_states_the_ticket(self):
        # spec: the needs-human PR comment SHALL state the ticket (the ticket
        # id must not sit only incidentally inside the PR title).
        body = needs_human_comment(1, self.T, 2)
        self.assertIn("Ticket BON-84", body)

    def test_needs_human_comment_without_ticket_does_not_claim_one(self):
        # REQUIRE_TICKET=0 mode drives unticketed PRs; the prose must not
        # claim a ticket that does not exist.
        body = needs_human_comment(1, "docs: housekeeping", 2)
        self.assertNotIn("this ticket", body)
        self.assertNotIn("BON-", body)


class TestSentinelScope(unittest.TestCase):
    """The driver sentinel skips comments only when it leads the comment.

    The documented contract (design D4 / tasks.md) puts the machine sentinel
    on the comment's FIRST line. A reviewer comment that merely quotes the
    sentinel mid-body must still parse as a review.
    """

    def test_sentinel_mid_body_still_parses_as_review(self):
        comment = ("## QA Report — **Verdict: approve**\n"
                   "Loop breaker noted: <!-- conveyor:needs-human -->.\n"
                   "No blockers.")
        self.assertEqual(parse_verdicts([comment]),
                         {"qa": "approve", "tech-pm": None})


if __name__ == "__main__":
    unittest.main()
