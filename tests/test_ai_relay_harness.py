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


def test_variant_commands_are_ignored(tmp_path: Path) -> None:
    variants = [
        "/relay start now",
        "/relay handoff now",
        "/relay plan now",
        "/relay verify now",
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
