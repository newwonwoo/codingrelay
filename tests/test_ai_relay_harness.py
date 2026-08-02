from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = REPO_ROOT / ".github" / "scripts" / "ai_relay_harness.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SPEC = importlib.util.spec_from_file_location("ai_relay_harness", HARNESS_PATH)
ai_relay_harness = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ai_relay_harness)


def load_fixture(name: str) -> dict[str, object]:
    fixture = json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(fixture, dict)
    return fixture


def write_event(repo_root: Path, body: str, issue_number: int = 9, is_pr: bool = False) -> Path:
    issue: dict[str, object] = {"number": issue_number}
    if is_pr:
        issue["pull_request"] = {"url": f"https://api.github.com/repos/owner/repo/pulls/{issue_number}"}
    event_path = repo_root / "event.json"
    event_path.write_text(json.dumps({"issue": issue, "comment": {"body": body}}), encoding="utf-8")
    return event_path


def write_fixture_event(tmp_path: Path, fixture_name: str) -> Path:
    event_path = tmp_path / fixture_name
    event_path.write_text((FIXTURES_DIR / fixture_name).read_text(encoding="utf-8"), encoding="utf-8")
    return event_path


class CommentThread:
    def __init__(self) -> None:
        self.comments: list[dict[str, object]] = []

    def post_comment(self, repository: str, issue_number: int, body: str, token: str) -> None:
        self.comments.append(
            {
                "repository": repository,
                "issue_number": issue_number,
                "body": body,
                "token": token,
            }
        )

    def list_comments(self, repository: str, issue_number: int, token: str) -> Sequence[Mapping[str, object]]:
        return self.comments

    @property
    def last_body(self) -> str:
        body = self.comments[-1]["body"]
        assert isinstance(body, str)
        return body


def handle_fixture(tmp_path: Path, fixture_name: str, thread: CommentThread) -> bool:
    return ai_relay_harness.handle_issue_comment_event(
        tmp_path,
        write_fixture_event(tmp_path, fixture_name),
        "owner/repo",
        "token",
        post_comment=thread.post_comment,
        list_comments=thread.list_comments,
    )


def test_load_relay_state_uses_ready_default_when_state_file_is_absent(tmp_path: Path) -> None:
    assert ai_relay_harness.load_relay_state(tmp_path) == {
        "status": "READY",
        "current_agent": "none",
        "next_agent": "none",
        "round": 0,
        "requires_human": False,
    }


def test_load_relay_state_reads_existing_state_file(tmp_path: Path) -> None:
    (tmp_path / "AI_RELAY_STATE.json").write_text(
        json.dumps(
            {
                "status": "WORKING",
                "current_agent": "codex",
                "next_agent": "claude",
                "round": 2,
                "requires_human": True,
            }
        ),
        encoding="utf-8",
    )

    assert ai_relay_harness.load_relay_state(tmp_path) == {
        "status": "WORKING",
        "current_agent": "codex",
        "next_agent": "claude",
        "round": 2,
        "requires_human": True,
    }


def test_format_status_response_matches_requested_shape() -> None:
    assert ai_relay_harness.format_status_response(ai_relay_harness.DEFAULT_RELAY_STATE) == (
        "[AI Relay Status]\n"
        "status: READY\n"
        "current_agent: none\n"
        "next_agent: none\n"
        "round: 0\n"
        "requires_human: false"
    )


def test_status_command_requires_exact_comment_body() -> None:
    assert ai_relay_harness.is_relay_status_comment(load_fixture("issue_comment_status.json")) is True
    assert ai_relay_harness.is_relay_status_comment({"comment": {"body": " /relay status"}}) is False
    assert ai_relay_harness.is_relay_status_comment({"comment": {"body": "/relay status "}}) is False
    assert ai_relay_harness.is_relay_status_comment({"comment": {"body": "/relay status\nnote: now"}}) is False
    assert ai_relay_harness.is_relay_status_comment({"comment": {"body": "/relay start"}}) is False


def test_start_command_requires_exact_first_line() -> None:
    assert ai_relay_harness.is_relay_start_comment(load_fixture("issue_comment_start.json")) is True
    assert ai_relay_harness.is_relay_start_comment({"comment": {"body": "/relay start"}}) is True
    assert ai_relay_harness.is_relay_start_comment({"comment": {"body": " /relay start"}}) is False
    assert ai_relay_harness.is_relay_start_comment({"comment": {"body": "/relay start "}}) is False
    assert ai_relay_harness.is_relay_start_comment({"comment": {"body": "/relay start now"}}) is False
    assert ai_relay_harness.is_relay_start_comment({"comment": {"body": "/relay status"}}) is False


def test_handoff_command_requires_exact_first_line() -> None:
    assert ai_relay_harness.is_relay_handoff_comment(load_fixture("issue_comment_handoff.json")) is True
    assert ai_relay_harness.is_relay_handoff_comment({"comment": {"body": "/relay handoff"}}) is True
    assert ai_relay_harness.is_relay_handoff_comment({"comment": {"body": " /relay handoff"}}) is False
    assert ai_relay_harness.is_relay_handoff_comment({"comment": {"body": "/relay handoff "}}) is False
    assert ai_relay_harness.is_relay_handoff_comment({"comment": {"body": "/relay handoff now"}}) is False
    assert ai_relay_harness.is_relay_handoff_comment({"comment": {"body": "/relay verify"}}) is False


def test_plan_command_requires_exact_first_line() -> None:
    assert ai_relay_harness.is_relay_plan_comment(load_fixture("issue_comment_plan.json")) is True
    assert ai_relay_harness.is_relay_plan_comment({"comment": {"body": "/relay plan"}}) is True
    assert ai_relay_harness.is_relay_plan_comment({"comment": {"body": " /relay plan"}}) is False
    assert ai_relay_harness.is_relay_plan_comment({"comment": {"body": "/relay plan "}}) is False
    assert ai_relay_harness.is_relay_plan_comment({"comment": {"body": "/relay plan now"}}) is False
    assert ai_relay_harness.is_relay_plan_comment({"comment": {"body": "/relay verify"}}) is False


def test_verify_command_requires_exact_first_line() -> None:
    assert ai_relay_harness.is_relay_verify_comment(load_fixture("issue_comment_verify.json")) is True
    assert ai_relay_harness.is_relay_verify_comment({"comment": {"body": "/relay verify"}}) is True
    assert ai_relay_harness.is_relay_verify_comment({"comment": {"body": " /relay verify"}}) is False
    assert ai_relay_harness.is_relay_verify_comment({"comment": {"body": "/relay verify "}}) is False
    assert ai_relay_harness.is_relay_verify_comment({"comment": {"body": "/relay verify now"}}) is False
    assert ai_relay_harness.is_relay_verify_comment({"comment": {"body": "/relay start"}}) is False


def test_dispatch_command_requires_exact_first_line() -> None:
    assert ai_relay_harness.is_relay_dispatch_comment(load_fixture("issue_comment_dispatch.json")) is True
    assert ai_relay_harness.is_relay_dispatch_comment({"comment": {"body": "/relay dispatch"}}) is True
    assert ai_relay_harness.is_relay_dispatch_comment({"comment": {"body": " /relay dispatch"}}) is False
    assert ai_relay_harness.is_relay_dispatch_comment({"comment": {"body": "/relay dispatch "}}) is False
    assert ai_relay_harness.is_relay_dispatch_comment({"comment": {"body": "/relay dispatch now"}}) is False
    assert ai_relay_harness.is_relay_dispatch_comment({"comment": {"body": "/relay verify"}}) is False


def test_build_start_state_parses_options() -> None:
    state = ai_relay_harness.build_start_state(load_fixture("issue_comment_start.json"))

    assert state == {
        "status": "WORKING",
        "current_agent": "claude",
        "next_agent": "codex",
        "round": 0,
        "goal": "local relay dry-run",
    }


def test_start_comment_contains_hidden_state_and_visible_response() -> None:
    state = {
        "status": "WORKING",
        "current_agent": "claude",
        "next_agent": "codex",
        "round": 0,
        "goal": "demo",
    }

    comment = ai_relay_harness.format_start_comment(state)

    assert comment.startswith("<!-- AI_RELAY_STATE\n")
    assert "\n-->\n\n[AI Relay Started]\n" in comment
    assert ai_relay_harness.extract_hidden_state(comment) == state
    assert "goal: demo" in comment


def test_handoff_comment_contains_swapped_state() -> None:
    previous_agent, state = ai_relay_harness.build_handoff_state(
        {
            "status": "WORKING",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 0,
            "goal": "demo",
        }
    )

    comment = ai_relay_harness.format_handoff_comment(previous_agent, state)

    assert previous_agent == "claude"
    assert ai_relay_harness.extract_hidden_state(comment) == {
        "status": "WORKING",
        "current_agent": "codex",
        "next_agent": "claude",
        "round": 1,
        "requires_human": False,
        "goal": "demo",
    }
    assert "[AI Relay Handoff]" in comment
    assert "previous_agent: claude" in comment
    assert "current_agent: codex" in comment


def test_plan_comment_contains_hidden_plan_and_visible_response() -> None:
    plan = ai_relay_harness.build_plan(load_fixture("issue_comment_plan.json"))

    comment = ai_relay_harness.format_plan_comment(plan)

    assert comment.startswith("<!-- AI_RELAY_PLAN\n")
    assert "\n-->\n\n[AI Relay Plan]\n" in comment
    assert ai_relay_harness.extract_hidden_plan(comment) == {
        "goal": "local relay validation",
        "scope": "dry-run fixture tests",
        "out_of_scope": "provider calls, skill loading",
        "done": "local verify prompt generated",
    }
    assert "goal: local relay validation" in comment
    assert "done: local verify prompt generated" in comment


def test_verify_comment_contains_latest_state_and_plan_prompt() -> None:
    state = {
        "status": "WORKING",
        "current_agent": "codex",
        "next_agent": "claude",
        "round": 1,
        "goal": "old state goal",
    }
    plan = {
        "goal": "local relay validation",
        "scope": "dry-run fixture tests",
        "out_of_scope": "provider calls, skill loading",
        "done": "local verify prompt generated",
    }

    comment = ai_relay_harness.format_verify_comment(state, plan)

    assert comment.startswith("<!-- AI_RELAY_STATE\n")
    assert "\n-->\n\n[AI Relay Verify]\n" in comment
    assert ai_relay_harness.extract_hidden_state(comment)["current_agent"] == "codex"
    assert "Self-verification prompt:" in comment
    assert "Goal: local relay validation" in comment
    assert "Scope: dry-run fixture tests" in comment
    assert "Done condition: local verify prompt generated" in comment
    assert "current_agent: codex" in comment


def test_dispatch_comment_contains_current_agent_work_prompt() -> None:
    state = {
        "status": "WORKING",
        "current_agent": "codex",
        "next_agent": "claude",
        "round": 1,
        "goal": "old state goal",
    }
    plan = {
        "goal": "local relay validation",
        "scope": "dry-run fixture tests",
        "out_of_scope": "provider calls, skill loading",
        "done": "local dispatch prompt generated",
    }

    comment = ai_relay_harness.format_dispatch_comment(state, plan)

    assert comment.startswith("<!-- AI_RELAY_STATE\n")
    assert "\n-->\n\n[AI Relay Dispatch]\n" in comment
    assert ai_relay_harness.extract_hidden_state(comment)["current_agent"] == "codex"
    assert "Dispatch prompt:" in comment
    assert "Target agent: codex" in comment
    assert "Goal: local relay validation" in comment
    assert "Scope: dry-run fixture tests" in comment
    assert "Done condition: local dispatch prompt generated" in comment
    assert "Do not perform provider calls, skill loading, agent mentions" in comment
    assert "@codex" not in comment
    assert "@claude" not in comment


def test_status_returns_ready_without_hidden_state(tmp_path: Path) -> None:
    thread = CommentThread()

    posted = handle_fixture(tmp_path, "issue_comment_status.json", thread)

    assert posted is True
    assert thread.last_body == (
        "[AI Relay Status]\n"
        "status: READY\n"
        "current_agent: none\n"
        "next_agent: none\n"
        "round: 0\n"
        "requires_human: false"
    )


def test_start_then_status_reads_working_hidden_state(tmp_path: Path) -> None:
    thread = CommentThread()

    assert handle_fixture(tmp_path, "issue_comment_start.json", thread) is True
    assert handle_fixture(tmp_path, "issue_comment_status.json", thread) is True

    assert ai_relay_harness.extract_hidden_state(thread.comments[0]["body"]) == {
        "status": "WORKING",
        "current_agent": "claude",
        "next_agent": "codex",
        "round": 0,
        "goal": "local relay dry-run",
    }
    assert thread.last_body == (
        "[AI Relay Status]\n"
        "status: WORKING\n"
        "current_agent: claude\n"
        "next_agent: codex\n"
        "round: 0\n"
        "requires_human: false"
    )


def test_start_handoff_then_status_reads_swapped_agents_and_incremented_round(tmp_path: Path) -> None:
    thread = CommentThread()

    assert handle_fixture(tmp_path, "issue_comment_start.json", thread) is True
    assert handle_fixture(tmp_path, "issue_comment_handoff.json", thread) is True
    assert handle_fixture(tmp_path, "issue_comment_status.json", thread) is True

    handoff_state = ai_relay_harness.extract_hidden_state(thread.comments[1]["body"])
    assert handoff_state == {
        "status": "WORKING",
        "current_agent": "codex",
        "next_agent": "claude",
        "round": 1,
        "requires_human": False,
        "goal": "local relay dry-run",
    }
    assert "previous_agent: claude" in thread.comments[1]["body"]
    assert thread.last_body == (
        "[AI Relay Status]\n"
        "status: WORKING\n"
        "current_agent: codex\n"
        "next_agent: claude\n"
        "round: 1\n"
        "requires_human: false"
    )


def test_plan_then_verify_reads_latest_state_and_plan(tmp_path: Path) -> None:
    thread = CommentThread()

    assert handle_fixture(tmp_path, "issue_comment_start.json", thread) is True
    assert handle_fixture(tmp_path, "issue_comment_handoff.json", thread) is True
    assert handle_fixture(tmp_path, "issue_comment_plan.json", thread) is True
    assert handle_fixture(tmp_path, "issue_comment_verify.json", thread) is True

    assert ai_relay_harness.extract_hidden_plan(thread.comments[2]["body"]) == {
        "goal": "local relay validation",
        "scope": "dry-run fixture tests",
        "out_of_scope": "provider calls, skill loading",
        "done": "local verify prompt generated",
    }
    assert "[AI Relay Verify]\nstatus: WORKING" in thread.last_body
    assert "current_agent: codex" in thread.last_body
    assert "round: 1" in thread.last_body
    assert "Goal: local relay validation" in thread.last_body
    assert "Scope: dry-run fixture tests" in thread.last_body
    assert "Done condition: local verify prompt generated" in thread.last_body


def test_plan_then_dispatch_reads_latest_state_and_plan(tmp_path: Path) -> None:
    thread = CommentThread()

    assert handle_fixture(tmp_path, "issue_comment_start.json", thread) is True
    assert handle_fixture(tmp_path, "issue_comment_handoff.json", thread) is True
    assert handle_fixture(tmp_path, "issue_comment_plan.json", thread) is True
    assert handle_fixture(tmp_path, "issue_comment_dispatch.json", thread) is True

    assert "[AI Relay Dispatch]\nstatus: WORKING" in thread.last_body
    assert "current_agent: codex" in thread.last_body
    assert "Target agent: codex" in thread.last_body
    assert "round: 1" in thread.last_body
    assert "Goal: local relay validation" in thread.last_body
    assert "Scope: dry-run fixture tests" in thread.last_body
    assert "Done condition: local verify prompt generated" in thread.last_body
    assert "@codex" not in thread.last_body
    assert "@claude" not in thread.last_body


def test_pr_comment_status_reads_hidden_state(tmp_path: Path) -> None:
    thread = CommentThread()
    start_state = {
        "status": "WORKING",
        "current_agent": "claude",
        "next_agent": "codex",
        "round": 0,
        "goal": "pr relay",
    }
    thread.comments.append({"body": ai_relay_harness.format_start_comment(start_state)})

    assert ai_relay_harness.is_pull_request_comment_event(load_fixture("pr_comment_status.json")) is True
    assert handle_fixture(tmp_path, "pr_comment_status.json", thread) is True

    assert thread.last_body == (
        "[AI Relay Status]\n"
        "status: WORKING\n"
        "current_agent: claude\n"
        "next_agent: codex\n"
        "round: 0\n"
        "requires_human: false"
    )


def test_pr_comment_verify_reads_hidden_state_and_plan(tmp_path: Path) -> None:
    thread = CommentThread()
    state = {
        "status": "WORKING",
        "current_agent": "codex",
        "next_agent": "claude",
        "round": 1,
        "goal": "pr relay",
    }
    plan = {
        "goal": "pr plan",
        "scope": "pr comment dry-run",
        "out_of_scope": "provider calls",
        "done": "verify prompt generated",
    }
    thread.comments.extend(
        [
            {"body": ai_relay_harness.format_start_comment(state)},
            {"body": ai_relay_harness.format_plan_comment(plan)},
        ]
    )

    assert ai_relay_harness.is_pull_request_comment_event(load_fixture("pr_comment_plan_verify.json")) is True
    assert handle_fixture(tmp_path, "pr_comment_plan_verify.json", thread) is True

    assert "[AI Relay Verify]" in thread.last_body
    assert "current_agent: codex" in thread.last_body
    assert "Goal: pr plan" in thread.last_body
    assert "Scope: pr comment dry-run" in thread.last_body


def test_accept_command_requires_exact_first_line() -> None:
    assert ai_relay_harness.is_relay_accept_comment(load_fixture("issue_comment_accept.json")) is True
    assert ai_relay_harness.is_relay_accept_comment({"comment": {"body": "/relay accept"}}) is True
    assert ai_relay_harness.is_relay_accept_comment({"comment": {"body": " /relay accept"}}) is False
    assert ai_relay_harness.is_relay_accept_comment({"comment": {"body": "/relay accept "}}) is False
    assert ai_relay_harness.is_relay_accept_comment({"comment": {"body": "/relay accept now"}}) is False
    assert ai_relay_harness.is_relay_accept_comment({"comment": {"body": "/relay reject"}}) is False


def test_reject_command_requires_exact_first_line() -> None:
    assert ai_relay_harness.is_relay_reject_comment(load_fixture("issue_comment_reject.json")) is True
    assert ai_relay_harness.is_relay_reject_comment({"comment": {"body": "/relay reject"}}) is True
    assert ai_relay_harness.is_relay_reject_comment({"comment": {"body": " /relay reject"}}) is False
    assert ai_relay_harness.is_relay_reject_comment({"comment": {"body": "/relay reject "}}) is False
    assert ai_relay_harness.is_relay_reject_comment({"comment": {"body": "/relay reject now"}}) is False
    assert ai_relay_harness.is_relay_reject_comment({"comment": {"body": "/relay accept"}}) is False


def test_accept_swaps_agents_and_increments_round() -> None:
    previous_agent, state = ai_relay_harness.build_accept_state(
        {
            "status": "RECEIVER_REVIEWING",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 0,
            "goal": "demo",
        }
    )
    assert previous_agent == "claude"
    assert state["current_agent"] == "codex"
    assert state["next_agent"] == "claude"
    assert state["round"] == 1
    assert state["status"] == "WORKING"


def test_reject_keeps_current_agent_and_bumps_reject_count() -> None:
    state = ai_relay_harness.build_reject_state(
        {
            "status": "RECEIVER_REVIEWING",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 1,
            "goal": "demo",
            "receiver_reject_count": 0,
        }
    )
    assert state["current_agent"] == "claude"
    assert state["next_agent"] == "codex"
    assert state["round"] == 1
    assert state["status"] == "REJECTED_BY_RECEIVER"
    assert state["receiver_reject_count"] == 1


def test_accept_comment_contains_hidden_state_and_visible_response() -> None:
    previous_agent, state = ai_relay_harness.build_accept_state(
        {
            "status": "RECEIVER_REVIEWING",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 0,
            "goal": "demo",
        }
    )
    comment = ai_relay_harness.format_accept_comment(previous_agent, state)
    assert comment.startswith("<!-- AI_RELAY_STATE\n")
    assert "\n-->\n\n[AI Relay Accepted]\n" in comment
    assert "previous_agent: claude" in comment
    assert "current_agent: codex" in comment
    assert "round: 1" in comment


def test_reject_comment_contains_self_fix_prompt_and_reason() -> None:
    state = ai_relay_harness.build_reject_state(
        {
            "status": "RECEIVER_REVIEWING",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 1,
            "goal": "demo",
            "receiver_reject_count": 0,
        }
    )
    comment = ai_relay_harness.format_reject_comment(state, "변경 파일 목록 누락")
    assert comment.startswith("<!-- AI_RELAY_STATE\n")
    assert "\n-->\n\n[AI Relay Rejected]\n" in comment
    assert "current_agent: claude" in comment
    assert "receiver_reject_count: 1" in comment
    assert "reason: 변경 파일 목록 누락" in comment
    assert "Self-fix prompt:" in comment
    assert "@claude" not in comment
    assert "@codex" not in comment


def test_start_handoff_accept_then_status_swaps_agents(tmp_path: Path) -> None:
    thread = CommentThread()

    assert handle_fixture(tmp_path, "issue_comment_start.json", thread) is True
    assert handle_fixture(tmp_path, "issue_comment_handoff.json", thread) is True
    assert handle_fixture(tmp_path, "issue_comment_accept.json", thread) is True
    assert handle_fixture(tmp_path, "issue_comment_status.json", thread) is True

    accept_state = ai_relay_harness.extract_hidden_state(thread.comments[2]["body"])
    assert accept_state["current_agent"] == "claude"
    assert accept_state["next_agent"] == "codex"
    assert accept_state["round"] == 2
    assert "[AI Relay Accepted]" in thread.comments[2]["body"]
    assert thread.last_body == (
        "[AI Relay Status]\n"
        "status: WORKING\n"
        "current_agent: claude\n"
        "next_agent: codex\n"
        "round: 2\n"
        "requires_human: false"
    )


def test_start_handoff_reject_then_status_keeps_current_agent(tmp_path: Path) -> None:
    thread = CommentThread()

    assert handle_fixture(tmp_path, "issue_comment_start.json", thread) is True
    assert handle_fixture(tmp_path, "issue_comment_handoff.json", thread) is True
    assert handle_fixture(tmp_path, "issue_comment_reject.json", thread) is True
    assert handle_fixture(tmp_path, "issue_comment_status.json", thread) is True

    reject_state = ai_relay_harness.extract_hidden_state(thread.comments[2]["body"])
    assert reject_state["current_agent"] == "codex"
    assert reject_state["next_agent"] == "claude"
    assert reject_state["status"] == "REJECTED_BY_RECEIVER"
    assert reject_state["receiver_reject_count"] == 1
    assert "reason: 변경 파일 목록 누락" in thread.comments[2]["body"]
    assert thread.last_body == (
        "[AI Relay Status]\n"
        "status: REJECTED_BY_RECEIVER\n"
        "current_agent: codex\n"
        "next_agent: claude\n"
        "round: 1\n"
        "requires_human: false"
    )


def write_minimal_baton(repo_root: Path, *, handoff_status: str = "PASS") -> None:
    (repo_root / "AI_BATON.md").write_text(
        "\n".join(
            [
                "# AI Baton",
                "",
                "## Task Goal",
                "- demo",
                "",
                "## Current Agent",
                "- claude",
                "",
                "## Next Agent",
                "- codex",
                "",
                "## Changed Files",
                "- harness.py",
                "",
                "## Evidence",
                "- pytest passed",
                "",
                f"## Handoff Status",
                handoff_status,
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_minimal_evidence(repo_root: Path) -> None:
    (repo_root / "AI_EVIDENCE.md").write_text(
        "\n".join(
            [
                "# AI Evidence",
                "",
                "## Commands Run",
                "- pytest -q",
                "",
                "## Results",
                "- 35 passed",
                "",
                "## Not Verified",
                "- live workflow",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_baton_gate_passes_when_all_required_sections_filled(tmp_path: Path) -> None:
    write_minimal_baton(tmp_path)
    assert ai_relay_harness.check_baton_required(tmp_path) == []


def test_baton_gate_reports_missing_file(tmp_path: Path) -> None:
    problems = ai_relay_harness.check_baton_required(tmp_path)
    assert problems == ["AI_BATON.md is missing."]


def test_baton_gate_reports_empty_section(tmp_path: Path) -> None:
    (tmp_path / "AI_BATON.md").write_text(
        "\n".join(
            [
                "# AI Baton",
                "## Task Goal",
                "-",
                "## Current Agent",
                "- claude",
                "## Next Agent",
                "- codex",
                "## Changed Files",
                "- f.py",
                "## Evidence",
                "- ok",
                "## Handoff Status",
                "PASS",
            ]
        ),
        encoding="utf-8",
    )
    problems = ai_relay_harness.check_baton_required(tmp_path)
    assert problems == ["AI_BATON.md section '## Task Goal' is empty."]


def test_baton_gate_reports_missing_section(tmp_path: Path) -> None:
    (tmp_path / "AI_BATON.md").write_text(
        "\n".join(
            [
                "# AI Baton",
                "## Task Goal",
                "- demo",
                "## Current Agent",
                "- claude",
                "## Next Agent",
                "- codex",
                "## Evidence",
                "- ok",
                "## Handoff Status",
                "PASS",
            ]
        ),
        encoding="utf-8",
    )
    problems = ai_relay_harness.check_baton_required(tmp_path)
    assert problems == ["AI_BATON.md missing section '## Changed Files'."]


def test_baton_gate_rejects_invalid_handoff_status(tmp_path: Path) -> None:
    write_minimal_baton(tmp_path, handoff_status="MAYBE")
    problems = ai_relay_harness.check_baton_required(tmp_path)
    assert any("Handoff Status" in p for p in problems)


def test_evidence_gate_passes_when_all_sections_filled(tmp_path: Path) -> None:
    write_minimal_evidence(tmp_path)
    assert ai_relay_harness.check_evidence_required(tmp_path) == []


def test_evidence_gate_reports_missing_file(tmp_path: Path) -> None:
    problems = ai_relay_harness.check_evidence_required(tmp_path)
    assert problems == ["AI_EVIDENCE.md is missing."]


def test_evaluate_handoff_gate_returns_pass_when_both_files_complete(tmp_path: Path) -> None:
    write_minimal_baton(tmp_path)
    write_minimal_evidence(tmp_path)
    verdict, reasons = ai_relay_harness.evaluate_handoff_gate(tmp_path)
    assert verdict == "PASS"
    assert reasons == []


def test_evaluate_handoff_gate_returns_block_when_baton_missing(tmp_path: Path) -> None:
    write_minimal_evidence(tmp_path)
    verdict, reasons = ai_relay_harness.evaluate_handoff_gate(tmp_path)
    assert verdict == "BLOCK"
    assert "AI_BATON.md is missing." in reasons


def test_verify_comment_includes_block_verdict_when_files_missing(tmp_path: Path) -> None:
    thread = CommentThread()
    assert handle_fixture(tmp_path, "issue_comment_verify.json", thread) is True
    body = thread.last_body
    assert "[AI Relay Verify]" in body
    assert "Handoff gate: BLOCK" in body
    assert "AI_BATON.md is missing." in body
    assert "AI_EVIDENCE.md is missing." in body


def test_verify_comment_includes_pass_verdict_when_files_complete(tmp_path: Path) -> None:
    write_minimal_baton(tmp_path)
    write_minimal_evidence(tmp_path)
    thread = CommentThread()
    assert handle_fixture(tmp_path, "issue_comment_verify.json", thread) is True
    body = thread.last_body
    assert "[AI Relay Verify]" in body
    assert "Handoff gate: PASS" in body
    assert "All required AI_BATON.md and AI_EVIDENCE.md sections are filled." in body


def test_repo_baton_and_evidence_pass_their_own_gate() -> None:
    assert ai_relay_harness.check_baton_required(REPO_ROOT) == []
    assert ai_relay_harness.check_evidence_required(REPO_ROOT) == []


def test_evaluate_limit_breach_returns_empty_when_within_limits() -> None:
    state = {
        "round": 1,
        "max_rounds": 3,
        "self_fix_count": 0,
        "max_self_fix": 2,
        "receiver_reject_count": 0,
        "max_receiver_reject": 1,
    }
    assert ai_relay_harness.evaluate_limit_breach(state) == []


def test_evaluate_limit_breach_flags_each_exceeded_counter() -> None:
    state = {
        "round": 5,
        "max_rounds": 3,
        "self_fix_count": 4,
        "max_self_fix": 2,
        "receiver_reject_count": 2,
        "max_receiver_reject": 1,
    }
    breaches = ai_relay_harness.evaluate_limit_breach(state)
    assert any("max_rounds" in b for b in breaches)
    assert any("max_self_fix" in b for b in breaches)
    assert any("max_receiver_reject" in b for b in breaches)


def test_evaluate_limit_breach_uses_default_limits_when_unset() -> None:
    breaches = ai_relay_harness.evaluate_limit_breach({"round": 99})
    assert any("max_rounds" in b for b in breaches)


def test_enforce_limits_promotes_status_to_human_required() -> None:
    state = ai_relay_harness.enforce_limits({"round": 99, "status": "WORKING", "current_agent": "claude"})
    assert state["status"] == "HUMAN_REQUIRED"
    assert state["requires_human"] is True


def test_enforce_limits_is_no_op_when_within_limits() -> None:
    base = {"round": 1, "status": "WORKING", "current_agent": "claude", "next_agent": "codex"}
    assert ai_relay_harness.enforce_limits(base) == base


def test_handoff_promotes_to_human_required_when_max_rounds_exceeded() -> None:
    _, state = ai_relay_harness.build_handoff_state(
        {
            "status": "WORKING",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 3,
            "max_rounds": 3,
            "goal": "demo",
        }
    )
    # round becomes 4 which exceeds max_rounds=3
    assert state["round"] == 4
    assert state["status"] == "HUMAN_REQUIRED"
    assert state["requires_human"] is True


def test_reject_promotes_to_human_required_when_max_reject_exceeded() -> None:
    state = ai_relay_harness.build_reject_state(
        {
            "status": "RECEIVER_REVIEWING",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 1,
            "receiver_reject_count": 1,
            "max_receiver_reject": 1,
            "goal": "demo",
        }
    )
    # count becomes 2 which exceeds max_receiver_reject=1
    assert state["receiver_reject_count"] == 2
    assert state["status"] == "HUMAN_REQUIRED"
    assert state["requires_human"] is True


def test_handle_event_returns_human_required_comment_when_state_is_locked(tmp_path: Path) -> None:
    write_minimal_baton(tmp_path)
    write_minimal_evidence(tmp_path)
    locked_state = ai_relay_harness.format_hidden_state_comment(
        {
            "status": "HUMAN_REQUIRED",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 4,
            "max_rounds": 3,
            "requires_human": True,
            "goal": "demo",
        }
    )
    thread = CommentThread()
    thread.comments.append({"body": locked_state})

    assert handle_fixture(tmp_path, "issue_comment_handoff.json", thread) is True
    body = thread.last_body
    assert "[AI Relay Human Required]" in body
    assert "round 4 exceeded max_rounds 3" in body
    assert "requires_human: true" in body
    # hidden state must remain HUMAN_REQUIRED, not advance
    locked = ai_relay_harness.extract_hidden_state(body)
    assert locked["status"] == "HUMAN_REQUIRED"
    assert locked["round"] == 4


def test_handle_event_status_command_still_responds_when_locked(tmp_path: Path) -> None:
    locked_state = ai_relay_harness.format_hidden_state_comment(
        {
            "status": "HUMAN_REQUIRED",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 4,
            "requires_human": True,
            "goal": "demo",
        }
    )
    thread = CommentThread()
    thread.comments.append({"body": locked_state})

    assert handle_fixture(tmp_path, "issue_comment_status.json", thread) is True
    body = thread.last_body
    # Status response shape — still readable to humans even when locked
    assert "[AI Relay Status]" in body
    assert "status: HUMAN_REQUIRED" in body
    assert "requires_human: true" in body


def test_stop_command_requires_exact_first_line() -> None:
    assert ai_relay_harness.is_relay_stop_comment(load_fixture("issue_comment_stop.json")) is True
    assert ai_relay_harness.is_relay_stop_comment({"comment": {"body": "/relay stop"}}) is True
    assert ai_relay_harness.is_relay_stop_comment({"comment": {"body": " /relay stop"}}) is False
    assert ai_relay_harness.is_relay_stop_comment({"comment": {"body": "/relay stop "}}) is False
    assert ai_relay_harness.is_relay_stop_comment({"comment": {"body": "/relay stopnow"}}) is False
    assert ai_relay_harness.is_relay_stop_comment({"comment": {"body": "/relay status"}}) is False


def test_fix_command_requires_exact_first_line() -> None:
    assert ai_relay_harness.is_relay_fix_comment(load_fixture("issue_comment_fix.json")) is True
    assert ai_relay_harness.is_relay_fix_comment({"comment": {"body": "/relay fix"}}) is True
    assert ai_relay_harness.is_relay_fix_comment({"comment": {"body": " /relay fix"}}) is False
    assert ai_relay_harness.is_relay_fix_comment({"comment": {"body": "/relay fix "}}) is False
    assert ai_relay_harness.is_relay_fix_comment({"comment": {"body": "/relay fix now"}}) is False
    assert ai_relay_harness.is_relay_fix_comment({"comment": {"body": "/relay verify"}}) is False


def test_build_stop_state_marks_done_with_reason() -> None:
    state = ai_relay_harness.build_stop_state(
        {"status": "WORKING", "current_agent": "claude", "next_agent": "codex", "round": 2},
        "scope changed",
    )
    assert state["status"] == "DONE"
    assert state["stop_reason"] == "scope changed"
    assert state["round"] == 2


def test_build_fix_state_increments_self_fix_count() -> None:
    state = ai_relay_harness.build_fix_state(
        {
            "status": "WORKING",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 1,
            "self_fix_count": 0,
        }
    )
    assert state["status"] == "NEEDS_SELF_FIX"
    assert state["self_fix_count"] == 1


def test_build_fix_state_promotes_to_human_required_when_max_self_fix_exceeded() -> None:
    state = ai_relay_harness.build_fix_state(
        {
            "status": "WORKING",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 1,
            "self_fix_count": 2,
            "max_self_fix": 2,
        }
    )
    # count becomes 3 which exceeds max_self_fix=2
    assert state["self_fix_count"] == 3
    assert state["status"] == "HUMAN_REQUIRED"
    assert state["requires_human"] is True


def test_format_self_fix_prompt_lists_block_reasons() -> None:
    prompt = ai_relay_harness.format_self_fix_prompt(
        {
            "status": "NEEDS_SELF_FIX",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 1,
            "self_fix_count": 1,
        },
        ["AI_BATON.md missing section '## Changed Files'.", "AI_EVIDENCE.md is missing."],
    )
    assert "Self-fix prompt:" in prompt
    assert "Target agent: claude" in prompt
    assert "AI_BATON.md missing section '## Changed Files'." in prompt
    assert "AI_EVIDENCE.md is missing." in prompt
    assert "@claude" not in prompt
    assert "@codex" not in prompt


def test_handle_event_stop_marks_state_done(tmp_path: Path) -> None:
    write_minimal_baton(tmp_path)
    write_minimal_evidence(tmp_path)
    thread = CommentThread()
    assert handle_fixture(tmp_path, "issue_comment_start.json", thread) is True
    assert handle_fixture(tmp_path, "issue_comment_stop.json", thread) is True

    body = thread.last_body
    assert "[AI Relay Stopped]" in body
    assert "reason: 작업 범위가 커져서 사람 검토 필요" in body
    stopped = ai_relay_harness.extract_hidden_state(body)
    assert stopped["status"] == "DONE"
    assert stopped["stop_reason"] == "작업 범위가 커져서 사람 검토 필요"


def test_handle_event_stop_works_even_when_locked(tmp_path: Path) -> None:
    locked_state = ai_relay_harness.format_hidden_state_comment(
        {
            "status": "HUMAN_REQUIRED",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 4,
            "max_rounds": 3,
            "requires_human": True,
        }
    )
    thread = CommentThread()
    thread.comments.append({"body": locked_state})
    assert handle_fixture(tmp_path, "issue_comment_stop.json", thread) is True
    body = thread.last_body
    assert "[AI Relay Stopped]" in body
    stopped = ai_relay_harness.extract_hidden_state(body)
    assert stopped["status"] == "DONE"


def test_handle_event_fix_emits_self_fix_prompt_with_gate_reasons(tmp_path: Path) -> None:
    # Intentionally do not write baton/evidence so the gate fails.
    thread = CommentThread()
    assert handle_fixture(tmp_path, "issue_comment_fix.json", thread) is True
    body = thread.last_body
    assert "[AI Relay Self-Fix]" in body
    assert "Self-fix prompt:" in body
    assert "AI_BATON.md is missing." in body
    assert "AI_EVIDENCE.md is missing." in body
    state = ai_relay_harness.extract_hidden_state(body)
    assert state["status"] == "NEEDS_SELF_FIX"
    assert state["self_fix_count"] == 1


def test_kakao_notify_skips_silently_when_no_webhook_url() -> None:
    sent: list[tuple[str, bytes]] = []
    sender = lambda url, payload: sent.append((url, payload))  # noqa: E731
    assert ai_relay_harness.kakao_notify("hi", webhook_url=None, sender=sender) is False
    assert ai_relay_harness.kakao_notify("hi", webhook_url="", sender=sender) is False
    assert sent == []


def test_kakao_notify_invokes_injected_sender_when_webhook_url_set() -> None:
    sent: list[tuple[str, bytes]] = []
    sender = lambda url, payload: sent.append((url, payload))  # noqa: E731
    assert (
        ai_relay_harness.kakao_notify(
            "[AI Relay 차단]\nreason: max_rounds exceeded",
            webhook_url="https://example.invalid/webhook",
            sender=sender,
        )
        is True
    )
    assert len(sent) == 1
    url, payload = sent[0]
    assert url == "https://example.invalid/webhook"
    body = json.loads(payload.decode("utf-8"))
    assert "차단" in body["text"]
    assert "max_rounds exceeded" in body["text"]


def test_build_start_state_folds_in_limits_from_state_file(tmp_path: Path) -> None:
    (tmp_path / "AI_RELAY_STATE.json").write_text(
        json.dumps(
            {
                "status": "READY",
                "current_agent": "none",
                "next_agent": "none",
                "round": 0,
                "max_rounds": 5,
                "max_self_fix": 4,
                "max_receiver_reject": 3,
                "requires_human": False,
            }
        ),
        encoding="utf-8",
    )
    state = ai_relay_harness.build_start_state({"comment": {"body": "/relay start"}}, tmp_path)
    assert state["max_rounds"] == 5
    assert state["max_self_fix"] == 4
    assert state["max_receiver_reject"] == 3


def test_build_start_state_omits_limits_when_no_state_file(tmp_path: Path) -> None:
    state = ai_relay_harness.build_start_state({"comment": {"body": "/relay start"}}, tmp_path)
    assert "max_rounds" not in state
    assert "max_self_fix" not in state


def test_extract_hidden_json_ignores_marker_inside_fenced_code_block() -> None:
    body = "\n".join(
        [
            "# Documentation example",
            "Some prose.",
            "```",
            "<!-- AI_RELAY_STATE",
            '{"status": "INJECTED"}',
            "-->",
            "```",
            "More prose.",
        ]
    )
    assert ai_relay_harness.extract_hidden_state(body) is None


def test_extract_hidden_json_requires_marker_at_column_zero() -> None:
    body = "    <!-- AI_RELAY_STATE\n" '{"status": "indented"}\n' "-->\n"
    assert ai_relay_harness.extract_hidden_state(body) is None


def test_extract_hidden_json_still_works_for_canonical_marker() -> None:
    state = {"status": "WORKING", "current_agent": "claude", "next_agent": "codex", "round": 0}
    body = ai_relay_harness.format_hidden_state_comment(state)
    assert ai_relay_harness.extract_hidden_state(body) == state


def test_latest_hidden_payload_prefers_highest_comment_id() -> None:
    older = ai_relay_harness.format_hidden_state_comment({"status": "WORKING", "round": 0})
    newer = ai_relay_harness.format_hidden_state_comment({"status": "WORKING", "round": 5})
    comments = [
        {"id": 200, "body": newer},
        {"id": 100, "body": older},
    ]
    payload = ai_relay_harness.latest_hidden_state(comments)
    assert payload is not None
    assert payload["round"] == 5


def test_latest_hidden_payload_skips_edited_comments() -> None:
    real = ai_relay_harness.format_hidden_state_comment({"status": "WORKING", "round": 1})
    hijacked = ai_relay_harness.format_hidden_state_comment({"status": "WORKING", "round": 99})
    comments = [
        # Edited old comment with a hijacked higher round
        {"id": 100, "body": hijacked, "created_at": "t1", "updated_at": "t2"},
        # Real recent comment
        {"id": 50, "body": real, "created_at": "t3", "updated_at": "t3"},
    ]
    payload = ai_relay_harness.latest_hidden_state(comments)
    assert payload is not None
    assert payload["round"] == 1


def test_latest_hidden_payload_falls_back_to_reverse_iteration_without_id() -> None:
    a = ai_relay_harness.format_hidden_state_comment({"status": "WORKING", "round": 1})
    b = ai_relay_harness.format_hidden_state_comment({"status": "WORKING", "round": 2})
    comments = [{"body": a}, {"body": b}]
    payload = ai_relay_harness.latest_hidden_state(comments)
    assert payload is not None
    assert payload["round"] == 2


def test_github_api_request_retries_on_url_error_then_succeeds() -> None:
    from urllib.error import URLError

    sleeps: list[float] = []
    attempts = {"count": 0}

    class FakeResponse:
        def __init__(self, body: bytes) -> None:
            self._body = body

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def read(self) -> bytes:
            return self._body

    def fake_opener(req):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise URLError("boom")
        return FakeResponse(b'{"ok": true}')

    result = ai_relay_harness.github_api_request(
        "https://api.github.com/test",
        "tok",
        backoff=(0.0, 0.0, 0.0),
        sleeper=lambda s: sleeps.append(s),
        opener=fake_opener,
    )
    assert result == {"ok": True}
    assert attempts["count"] == 3
    assert sleeps == [0.0, 0.0]


def test_github_api_request_raises_relay_harness_error_after_exhaustion() -> None:
    from urllib.error import URLError

    def always_fails(req):
        raise URLError("perma-down")

    try:
        ai_relay_harness.github_api_request(
            "https://api.github.com/test",
            "tok",
            backoff=(0.0,),
            sleeper=lambda s: None,
            opener=always_fails,
        )
    except ai_relay_harness.RelayHarnessError as exc:
        assert "perma-down" in str(exc)
    else:
        raise AssertionError("expected RelayHarnessError after retry exhaustion")


def test_start_blocked_when_prior_state_is_done_without_force(tmp_path: Path) -> None:
    done_state = ai_relay_harness.format_hidden_state_comment(
        {
            "status": "DONE",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 2,
            "goal": "old task",
        }
    )
    thread = CommentThread()
    thread.comments.append({"id": 1, "body": done_state})

    assert handle_fixture(tmp_path, "issue_comment_start.json", thread) is True
    body = thread.last_body
    assert "[AI Relay Start Blocked]" in body
    # Hidden state should still reflect the prior DONE, not a fresh WORKING
    extracted = ai_relay_harness.extract_hidden_state(body)
    assert extracted["status"] == "DONE"


def test_start_with_force_true_resumes_and_carries_counters(tmp_path: Path) -> None:
    done_state = ai_relay_harness.format_hidden_state_comment(
        {
            "status": "DONE",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 2,
            "self_fix_count": 1,
            "receiver_reject_count": 1,
            "max_rounds": 3,
            "goal": "old task",
        }
    )
    thread = CommentThread()
    thread.comments.append({"id": 1, "body": done_state})
    event_path = write_event(
        tmp_path,
        "/relay start\nforce: true\ngoal: new task",
        issue_number=42,
    )
    assert ai_relay_harness.handle_issue_comment_event(
        tmp_path,
        event_path,
        "owner/repo",
        "token",
        post_comment=thread.post_comment,
        list_comments=thread.list_comments,
    ) is True
    body = thread.last_body
    assert "[AI Relay Started]" in body
    new_state = ai_relay_harness.extract_hidden_state(body)
    assert new_state["status"] == "WORKING"
    assert new_state["round"] == 2
    assert new_state["self_fix_count"] == 1
    assert new_state["receiver_reject_count"] == 1
    assert new_state["max_rounds"] == 3
    assert new_state["goal"] == "new task"


def test_main_posts_error_comment_when_relay_harness_error_raised(tmp_path: Path, monkeypatch, capsys) -> None:
    event_path = write_fixture_event(tmp_path, "issue_comment_status.json")
    posted: list[tuple[str, int, str, str]] = []

    def boom(*_a, **_kw):
        raise ai_relay_harness.RelayHarnessError("network exploded")

    def record_post(repository, issue_number, body, token):
        posted.append((repository, issue_number, body, token))

    monkeypatch.setattr(ai_relay_harness, "list_issue_comments", boom)
    monkeypatch.setattr(ai_relay_harness, "post_issue_comment", record_post)

    exit_code = ai_relay_harness.main(
        [
            str(tmp_path),
            "--event-path",
            str(event_path),
            "--repository",
            "owner/repo",
            "--token",
            "tok",
        ]
    )
    assert exit_code == 1
    assert len(posted) == 1
    body = posted[0][2]
    assert "[AI Relay Error]" in body
    assert "network exploded" in body


def test_github_api_request_retries_on_403_when_secondary_rate_limit_exhausted() -> None:
    from urllib.error import HTTPError
    from email.message import Message

    sleeps: list[float] = []
    attempts = {"count": 0}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def read(self) -> bytes:
            return b'{"ok": true}'

    rate_limit_headers = Message()
    rate_limit_headers["x-ratelimit-remaining"] = "0"

    def flaky_opener(req):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise HTTPError(
                url="https://api.github.com/test",
                code=403,
                msg="Forbidden",
                hdrs=rate_limit_headers,
                fp=None,
            )
        return FakeResponse()

    result = ai_relay_harness.github_api_request(
        "https://api.github.com/test",
        "tok",
        backoff=(0.0,),
        sleeper=lambda s: sleeps.append(s),
        opener=flaky_opener,
    )
    assert result == {"ok": True}
    assert attempts["count"] == 2


def test_github_api_request_403_without_rate_limit_header_is_not_retried() -> None:
    from urllib.error import HTTPError
    from email.message import Message

    attempts = {"count": 0}

    def always_forbidden(req):
        attempts["count"] += 1
        raise HTTPError(
            url="https://api.github.com/test",
            code=403,
            msg="Forbidden",
            hdrs=Message(),
            fp=None,
        )

    try:
        ai_relay_harness.github_api_request(
            "https://api.github.com/test",
            "tok",
            backoff=(0.0, 0.0),
            sleeper=lambda s: None,
            opener=always_forbidden,
        )
    except ai_relay_harness.RelayHarnessError as exc:
        assert "HTTP 403" in str(exc)
    else:
        raise AssertionError("expected RelayHarnessError for non-rate-limit 403")
    assert attempts["count"] == 1


def test_github_api_request_honors_retry_after_header() -> None:
    from urllib.error import HTTPError
    from email.message import Message

    sleeps: list[float] = []
    attempts = {"count": 0}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def read(self) -> bytes:
            return b'{"ok": true}'

    retry_headers = Message()
    retry_headers["Retry-After"] = "17"

    def flaky_opener(req):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise HTTPError(
                url="https://api.github.com/test",
                code=429,
                msg="Too Many Requests",
                hdrs=retry_headers,
                fp=None,
            )
        return FakeResponse()

    result = ai_relay_harness.github_api_request(
        "https://api.github.com/test",
        "tok",
        backoff=(1.0,),  # small configured backoff, header says 17
        sleeper=lambda s: sleeps.append(s),
        opener=flaky_opener,
    )
    assert result == {"ok": True}
    assert sleeps == [17.0]


def test_github_api_request_ignores_malformed_retry_after() -> None:
    from urllib.error import HTTPError
    from email.message import Message

    sleeps: list[float] = []
    attempts = {"count": 0}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def read(self) -> bytes:
            return b'{"ok": true}'

    bad_headers = Message()
    bad_headers["Retry-After"] = "not-a-number"

    def flaky_opener(req):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise HTTPError(
                url="https://api.github.com/test",
                code=503,
                msg="Service Unavailable",
                hdrs=bad_headers,
                fp=None,
            )
        return FakeResponse()

    result = ai_relay_harness.github_api_request(
        "https://api.github.com/test",
        "tok",
        backoff=(3.0,),
        sleeper=lambda s: sleeps.append(s),
        opener=flaky_opener,
    )
    assert result == {"ok": True}
    assert sleeps == [3.0]  # configured backoff, malformed header ignored


def test_kakao_notify_passes_timeout_to_urlopen(monkeypatch) -> None:
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

    def fake_urlopen(req, timeout=None, *_a, **_kw):
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(ai_relay_harness.request, "urlopen", fake_urlopen)

    result = ai_relay_harness.kakao_notify("hi", webhook_url="https://kakao.example/hook")
    assert result is True
    assert captured["timeout"] == 10


def test_kakao_notify_skips_silently_without_webhook(capsys) -> None:
    sent: list[tuple[str, bytes]] = []

    def sender(url: str, body: bytes) -> None:
        sent.append((url, body))

    result = ai_relay_harness.kakao_notify("hi", webhook_url=None, sender=sender)
    assert result is False
    assert sent == []
    captured = capsys.readouterr()
    assert captured.err == ""


def test_kakao_notify_returns_true_on_successful_send() -> None:
    sent: list[tuple[str, bytes]] = []

    def sender(url: str, body: bytes) -> None:
        sent.append((url, body))

    result = ai_relay_harness.kakao_notify(
        "ping",
        webhook_url="https://kakao.example/hook",
        sender=sender,
    )
    assert result is True
    assert len(sent) == 1
    assert sent[0][0] == "https://kakao.example/hook"
    assert b"ping" in sent[0][1]


def test_kakao_notify_returns_false_and_logs_on_url_error(capsys) -> None:
    from urllib.error import URLError

    def boom(url: str, body: bytes) -> None:
        raise URLError("kakao-down")

    result = ai_relay_harness.kakao_notify(
        "alert",
        webhook_url="https://kakao.example/hook",
        sender=boom,
    )
    assert result is False
    captured = capsys.readouterr()
    assert "kakao_notify delivery failed" in captured.err
    assert "kakao-down" in captured.err


def test_kakao_notify_swallows_unexpected_errors(capsys) -> None:
    def weird(url: str, body: bytes) -> None:
        raise RuntimeError("nope")

    result = ai_relay_harness.kakao_notify(
        "alert",
        webhook_url="https://kakao.example/hook",
        sender=weird,
    )
    assert result is False
    captured = capsys.readouterr()
    assert "kakao_notify unexpected error" in captured.err
    assert "nope" in captured.err


def test_human_required_branch_returns_true_even_when_kakao_fails(tmp_path: Path, monkeypatch) -> None:
    """The relay state must be persisted to GitHub even if kakao is unreachable."""
    from urllib.error import URLError

    locked_state = ai_relay_harness.format_hidden_state_comment(
        {
            "status": "WORKING",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 99,
            "max_rounds": 3,
            "requires_human": False,
        }
    )
    thread = CommentThread()
    thread.comments.append({"id": 1, "body": locked_state})

    monkeypatch.setenv("KAKAO_WEBHOOK_URL", "https://kakao.example/hook")

    real_urlopen = ai_relay_harness.request.urlopen

    def fake_urlopen(req, *a, **kw):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "kakao.example" in url:
            raise URLError("kakao-down")
        return real_urlopen(req, *a, **kw)

    monkeypatch.setattr(ai_relay_harness.request, "urlopen", fake_urlopen)

    event_path = write_event(tmp_path, "/relay handoff", issue_number=42)
    posted = ai_relay_harness.handle_issue_comment_event(
        tmp_path,
        event_path,
        "owner/repo",
        "token",
        post_comment=thread.post_comment,
        list_comments=thread.list_comments,
    )
    assert posted is True
    assert "[AI Relay 사람 판단 필요" in thread.last_body or "HUMAN_REQUIRED" in thread.last_body


def test_workflow_pull_request_test_gate_runs_pytest() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "ai-relay-tests.yml").read_text(encoding="utf-8")

    assert "pull_request:" in workflow
    assert "py_compile" in workflow
    assert "pytest" in workflow


def test_variant_commands_are_ignored(tmp_path: Path) -> None:
    variants = [
        "/relay start now",
        "/relay handoff now",
        "/relay plan now",
        "/relay verify now",
        "/relay dispatch now",
        "/relay accept now",
        "/relay reject now",
        "/relay stop now",
        "/relay fix now",
    ]
    for index, body in enumerate(variants):
        thread = CommentThread()
        posted = ai_relay_harness.handle_issue_comment_event(
            tmp_path,
            write_event(tmp_path, body, issue_number=index + 1),
            "owner/repo",
            "token",
            post_comment=thread.post_comment,
            list_comments=thread.list_comments,
        )
        assert posted is False
        assert thread.comments == []


def test_dry_run_prints_comment_without_token_or_github_api(tmp_path: Path, capsys) -> None:
    event_path = write_fixture_event(tmp_path, "issue_comment_status.json")
    summary_path = tmp_path / "summary.md"

    exit_code = ai_relay_harness.main(
        [
            str(tmp_path),
            "--event-path",
            str(event_path),
            "--repository",
            "owner/repo",
            "--dry-run",
            "--summary",
            str(summary_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "[AI Relay Dry Run]" in captured.out
    assert "[AI Relay Status]" in captured.out
    assert "GITHUB_TOKEN is required" not in captured.out
    assert "[AI Relay Status]" in summary_path.read_text(encoding="utf-8")


def test_dry_run_can_read_comments_fixture_without_github_api(tmp_path: Path, capsys) -> None:
    event_path = write_fixture_event(tmp_path, "issue_comment_status.json")
    state = {
        "status": "WORKING",
        "current_agent": "claude",
        "next_agent": "codex",
        "round": 0,
        "goal": "fixture state",
    }
    comments_path = tmp_path / "comments.json"
    comments_path.write_text(json.dumps([{"body": ai_relay_harness.format_start_comment(state)}]), encoding="utf-8")

    exit_code = ai_relay_harness.main(
        [
            str(tmp_path),
            "--event-path",
            str(event_path),
            "--repository",
            "owner/repo",
            "--dry-run",
            "--comments-path",
            str(comments_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "status: WORKING" in captured.out
    assert "current_agent: claude" in captured.out


def test_workflow_checks_out_pr_head_before_reading_state() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "ai-relay.yml").read_text(encoding="utf-8")

    assert "workflow_run" not in workflow
    assert "uses: actions/github-script@v7" in workflow
    assert "github.rest.pulls.get" in workflow
    assert "pull.head.repo.full_name" in workflow
    assert "pull.head.sha" in workflow
    assert "repository: ${{ steps.checkout-target.outputs.repository }}" in workflow
    assert "ref: ${{ steps.checkout-target.outputs.ref }}" in workflow
