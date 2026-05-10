from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Mapping, Sequence


HARNESS_PATH = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "ai_relay_harness.py"
SPEC = importlib.util.spec_from_file_location("ai_relay_harness", HARNESS_PATH)
ai_relay_harness = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ai_relay_harness)


def write_event(repo_root: Path, body: str, issue_number: int = 9) -> Path:
    event_path = repo_root / "event.json"
    event_path.write_text(
        json.dumps(
            {
                "issue": {"number": issue_number},
                "comment": {"body": body},
            }
        ),
        encoding="utf-8",
    )
    return event_path


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
    assert ai_relay_harness.is_relay_status_comment({"comment": {"body": "/relay status"}}) is True
    assert ai_relay_harness.is_relay_status_comment({"comment": {"body": " /relay status"}}) is False
    assert ai_relay_harness.is_relay_status_comment({"comment": {"body": "/relay status "}}) is False
    assert ai_relay_harness.is_relay_status_comment({"comment": {"body": "/relay start"}}) is False
    assert ai_relay_harness.is_relay_status_comment({"comment": {"body": "/relay verify"}}) is False


def test_start_command_requires_exact_first_line() -> None:
    assert ai_relay_harness.is_relay_start_comment({"comment": {"body": "/relay start"}}) is True
    assert ai_relay_harness.is_relay_start_comment({"comment": {"body": "/relay start\ngoal: ship"}}) is True
    assert ai_relay_harness.is_relay_start_comment({"comment": {"body": " /relay start"}}) is False
    assert ai_relay_harness.is_relay_start_comment({"comment": {"body": "/relay start "}}) is False
    assert ai_relay_harness.is_relay_start_comment({"comment": {"body": "/relay verify"}}) is False


def test_verify_command_requires_exact_first_line() -> None:
    assert ai_relay_harness.is_relay_verify_comment({"comment": {"body": "/relay verify"}}) is True
    assert ai_relay_harness.is_relay_verify_comment({"comment": {"body": "/relay verify\nnote: check"}}) is True
    assert ai_relay_harness.is_relay_verify_comment({"comment": {"body": " /relay verify"}}) is False
    assert ai_relay_harness.is_relay_verify_comment({"comment": {"body": "/relay verify "}}) is False
    assert ai_relay_harness.is_relay_verify_comment({"comment": {"body": "/relay verify now"}}) is False
    assert ai_relay_harness.is_relay_verify_comment({"comment": {"body": "/relay start"}}) is False


def test_plan_command_requires_exact_first_line() -> None:
    assert ai_relay_harness.is_relay_plan_comment({"comment": {"body": "/relay plan"}}) is True
    assert ai_relay_harness.is_relay_plan_comment({"comment": {"body": "/relay plan\ngoal: ship"}}) is True
    assert ai_relay_harness.is_relay_plan_comment({"comment": {"body": " /relay plan"}}) is False
    assert ai_relay_harness.is_relay_plan_comment({"comment": {"body": "/relay plan "}}) is False
    assert ai_relay_harness.is_relay_plan_comment({"comment": {"body": "/relay plan now"}}) is False
    assert ai_relay_harness.is_relay_plan_comment({"comment": {"body": "/relay dispatch"}}) is False


def test_dispatch_command_requires_exact_first_line() -> None:
    assert ai_relay_harness.is_relay_dispatch_comment({"comment": {"body": "/relay dispatch"}}) is True
    assert ai_relay_harness.is_relay_dispatch_comment({"comment": {"body": "/relay dispatch\nnote: go"}}) is True
    assert ai_relay_harness.is_relay_dispatch_comment({"comment": {"body": " /relay dispatch"}}) is False
    assert ai_relay_harness.is_relay_dispatch_comment({"comment": {"body": "/relay dispatch "}}) is False
    assert ai_relay_harness.is_relay_dispatch_comment({"comment": {"body": "/relay dispatch now"}}) is False
    assert ai_relay_harness.is_relay_dispatch_comment({"comment": {"body": "/relay plan"}}) is False


def test_build_start_state_uses_defaults() -> None:
    state = ai_relay_harness.build_start_state({"comment": {"body": "/relay start"}})

    assert state == {
        "status": "WORKING",
        "current_agent": "claude",
        "next_agent": "codex",
        "round": 0,
        "goal": "",
    }


def test_build_start_state_parses_options() -> None:
    state = ai_relay_harness.build_start_state(
        {
            "comment": {
                "body": "/relay start\nstart_agent: codex\nnext_agent=claude\ngoal: fix relay status"
            }
        }
    )

    assert state == {
        "status": "WORKING",
        "current_agent": "codex",
        "next_agent": "claude",
        "round": 0,
        "goal": "fix relay status",
    }


def test_build_plan_state_overlays_plan_fields() -> None:
    state = ai_relay_harness.build_plan_state(
        {
            "status": "WORKING",
            "current_agent": "codex",
            "next_agent": "claude",
            "round": 1,
            "goal": "old",
        },
        {
            "comment": {
                "body": (
                    "/relay plan\n"
                    "goal: relay dispatch 구현\n"
                    "scope: 현재 state와 plan을 읽어 작업 프롬프트 생성\n"
                    "out_of_scope: 실제 AI 호출, skill loading\n"
                    "done: dispatch 프롬프트 댓글이 생성되면 성공"
                )
            }
        },
    )

    assert state == {
        "status": "WORKING",
        "current_agent": "codex",
        "next_agent": "claude",
        "round": 1,
        "goal": "relay dispatch 구현",
        "scope": "현재 state와 plan을 읽어 작업 프롬프트 생성",
        "out_of_scope": "실제 AI 호출, skill loading",
        "done": "dispatch 프롬프트 댓글이 생성되면 성공",
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


def test_verify_comment_contains_hidden_state_and_self_verification_prompt() -> None:
    state = {
        "status": "WORKING",
        "current_agent": "claude",
        "next_agent": "codex",
        "round": 0,
        "goal": "/relay verify 구현",
        "scope": "자기검증 프롬프트 생성",
        "out_of_scope": "실제 AI 호출, skill loading",
        "done": "verify 댓글이 생성되면 성공",
    }

    comment = ai_relay_harness.format_verify_comment(state)

    assert comment.startswith("<!-- AI_RELAY_STATE\n")
    assert "\n-->\n\n[AI Relay Verify]\n" in comment
    assert ai_relay_harness.extract_hidden_state(comment) == state
    assert "Self-verification prompt:" in comment
    assert "Goal: /relay verify 구현" in comment
    assert "Scope: 자기검증 프롬프트 생성" in comment
    assert "Out of scope: 실제 AI 호출, skill loading" in comment
    assert "Done condition: verify 댓글이 생성되면 성공" in comment
    assert "Report PASS or BLOCK" in comment


def test_plan_comment_contains_hidden_state_and_plan_response() -> None:
    state = {
        "status": "WORKING",
        "current_agent": "codex",
        "next_agent": "claude",
        "round": 1,
        "goal": "relay dispatch 구현",
        "scope": "현재 state와 plan을 읽어 작업 프롬프트 생성",
        "out_of_scope": "실제 AI 호출, skill loading",
        "done": "dispatch 프롬프트 댓글이 생성되면 성공",
    }

    comment = ai_relay_harness.format_plan_comment(state)

    assert comment.startswith("<!-- AI_RELAY_STATE\n")
    assert "\n-->\n\n[AI Relay Plan]\n" in comment
    assert ai_relay_harness.extract_hidden_state(comment) == state
    assert "goal: relay dispatch 구현" in comment
    assert "scope: 현재 state와 plan을 읽어 작업 프롬프트 생성" in comment
    assert "done: dispatch 프롬프트 댓글이 생성되면 성공" in comment


def test_dispatch_comment_contains_hidden_state_and_dispatch_prompt() -> None:
    state = {
        "status": "WORKING",
        "current_agent": "codex",
        "next_agent": "claude",
        "round": 1,
        "goal": "relay dispatch 구현",
        "scope": "현재 state와 plan을 읽어 작업 프롬프트 생성",
        "out_of_scope": "실제 AI 호출, skill loading",
        "done": "dispatch 프롬프트 댓글이 생성되면 성공",
    }

    comment = ai_relay_harness.format_dispatch_comment(state)

    assert comment.startswith("<!-- AI_RELAY_STATE\n")
    assert "\n-->\n\n[AI Relay Dispatch]\n" in comment
    assert ai_relay_harness.extract_hidden_state(comment) == state
    assert "Dispatch prompt:" in comment
    assert "Current agent: codex" in comment
    assert "Goal: relay dispatch 구현" in comment
    assert "Scope: 현재 state와 plan을 읽어 작업 프롬프트 생성" in comment
    assert "Out of scope: 실제 AI 호출, skill loading" in comment
    assert "Done condition: dispatch 프롬프트 댓글이 생성되면 성공" in comment
    assert "Do not perform provider calls" in comment


def test_handle_issue_comment_event_posts_status_from_latest_hidden_state(tmp_path: Path) -> None:
    event_path = write_event(tmp_path, "/relay status", issue_number=42)
    hidden_comment = ai_relay_harness.format_hidden_state_comment(
        {
            "status": "WORKING",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 0,
            "goal": "from hidden state",
        }
    )
    posted_comments: list[tuple[str, int, str, str]] = []

    def record_comment(repository: str, issue_number: int, body: str, token: str) -> None:
        posted_comments.append((repository, issue_number, body, token))

    def list_comments(repository: str, issue_number: int, token: str) -> Sequence[Mapping[str, object]]:
        return [{"body": "old"}, {"body": hidden_comment}]

    posted = ai_relay_harness.handle_issue_comment_event(
        tmp_path,
        event_path,
        "owner/repo",
        "token",
        post_comment=record_comment,
        list_comments=list_comments,
    )

    assert posted is True
    assert posted_comments == [
        (
            "owner/repo",
            42,
            "[AI Relay Status]\n"
            "status: WORKING\n"
            "current_agent: claude\n"
            "next_agent: codex\n"
            "round: 0\n"
            "requires_human: false",
            "token",
        )
    ]


def test_handle_issue_comment_event_posts_status_ready_fallback_without_hidden_state(tmp_path: Path) -> None:
    event_path = write_event(tmp_path, "/relay status", issue_number=42)
    posted_comments: list[tuple[str, int, str, str]] = []

    def record_comment(repository: str, issue_number: int, body: str, token: str) -> None:
        posted_comments.append((repository, issue_number, body, token))

    def list_comments(repository: str, issue_number: int, token: str) -> Sequence[Mapping[str, object]]:
        return []

    posted = ai_relay_harness.handle_issue_comment_event(
        tmp_path,
        event_path,
        "owner/repo",
        "token",
        post_comment=record_comment,
        list_comments=list_comments,
    )

    assert posted is True
    assert posted_comments == [
        (
            "owner/repo",
            42,
            "[AI Relay Status]\n"
            "status: READY\n"
            "current_agent: none\n"
            "next_agent: none\n"
            "round: 0\n"
            "requires_human: false",
            "token",
        )
    ]


def test_handle_issue_comment_event_starts_relay_with_hidden_state(tmp_path: Path) -> None:
    event_path = write_event(
        tmp_path,
        "/relay start\nstart_agent: codex\nnext_agent: claude\ngoal: implement start",
        issue_number=42,
    )
    posted_comments: list[tuple[str, int, str, str]] = []

    def record_comment(repository: str, issue_number: int, body: str, token: str) -> None:
        posted_comments.append((repository, issue_number, body, token))

    posted = ai_relay_harness.handle_issue_comment_event(
        tmp_path,
        event_path,
        "owner/repo",
        "token",
        post_comment=record_comment,
    )

    assert posted is True
    assert len(posted_comments) == 1
    repository, issue_number, body, token = posted_comments[0]
    assert (repository, issue_number, token) == ("owner/repo", 42, "token")
    assert ai_relay_harness.extract_hidden_state(body) == {
        "status": "WORKING",
        "current_agent": "codex",
        "next_agent": "claude",
        "round": 0,
        "goal": "implement start",
    }
    assert "[AI Relay Started]\nstatus: WORKING" in body
    assert "current_agent: codex" in body
    assert "next_agent: claude" in body
    assert "goal: implement start" in body


def test_handle_issue_comment_event_posts_plan_from_latest_hidden_state(tmp_path: Path) -> None:
    event_path = write_event(
        tmp_path,
        (
            "/relay plan\n"
            "goal: relay dispatch 구현\n"
            "scope: 현재 state와 plan을 읽어 작업 프롬프트 생성\n"
            "out_of_scope: 실제 AI 호출, skill loading\n"
            "done: dispatch 프롬프트 댓글이 생성되면 성공"
        ),
        issue_number=42,
    )
    hidden_comment = ai_relay_harness.format_hidden_state_comment(
        {
            "status": "WORKING",
            "current_agent": "codex",
            "next_agent": "claude",
            "round": 1,
            "goal": "old",
        }
    )
    posted_comments: list[tuple[str, int, str, str]] = []

    def record_comment(repository: str, issue_number: int, body: str, token: str) -> None:
        posted_comments.append((repository, issue_number, body, token))

    def list_comments(repository: str, issue_number: int, token: str) -> Sequence[Mapping[str, object]]:
        return [{"body": "old"}, {"body": hidden_comment}]

    posted = ai_relay_harness.handle_issue_comment_event(
        tmp_path,
        event_path,
        "owner/repo",
        "token",
        post_comment=record_comment,
        list_comments=list_comments,
    )

    assert posted is True
    assert len(posted_comments) == 1
    repository, issue_number, body, token = posted_comments[0]
    assert (repository, issue_number, token) == ("owner/repo", 42, "token")
    assert ai_relay_harness.extract_hidden_state(body) == {
        "status": "WORKING",
        "current_agent": "codex",
        "next_agent": "claude",
        "round": 1,
        "goal": "relay dispatch 구현",
        "scope": "현재 state와 plan을 읽어 작업 프롬프트 생성",
        "out_of_scope": "실제 AI 호출, skill loading",
        "done": "dispatch 프롬프트 댓글이 생성되면 성공",
    }
    assert "[AI Relay Plan]\nstatus: WORKING" in body
    assert "current_agent: codex" in body
    assert "scope: 현재 state와 plan을 읽어 작업 프롬프트 생성" in body


def test_handle_issue_comment_event_posts_dispatch_from_latest_hidden_state(tmp_path: Path) -> None:
    event_path = write_event(tmp_path, "/relay dispatch", issue_number=42)
    hidden_comment = ai_relay_harness.format_hidden_state_comment(
        {
            "status": "WORKING",
            "current_agent": "codex",
            "next_agent": "claude",
            "round": 1,
            "goal": "relay dispatch 구현",
            "scope": "현재 state와 plan을 읽어 작업 프롬프트 생성",
            "out_of_scope": "실제 AI 호출, skill loading",
            "done": "dispatch 프롬프트 댓글이 생성되면 성공",
        }
    )
    posted_comments: list[tuple[str, int, str, str]] = []

    def record_comment(repository: str, issue_number: int, body: str, token: str) -> None:
        posted_comments.append((repository, issue_number, body, token))

    def list_comments(repository: str, issue_number: int, token: str) -> Sequence[Mapping[str, object]]:
        return [{"body": "old"}, {"body": hidden_comment}]

    posted = ai_relay_harness.handle_issue_comment_event(
        tmp_path,
        event_path,
        "owner/repo",
        "token",
        post_comment=record_comment,
        list_comments=list_comments,
    )

    assert posted is True
    assert len(posted_comments) == 1
    repository, issue_number, body, token = posted_comments[0]
    assert (repository, issue_number, token) == ("owner/repo", 42, "token")
    assert ai_relay_harness.extract_hidden_state(body) == {
        "status": "WORKING",
        "current_agent": "codex",
        "next_agent": "claude",
        "round": 1,
        "goal": "relay dispatch 구현",
        "scope": "현재 state와 plan을 읽어 작업 프롬프트 생성",
        "out_of_scope": "실제 AI 호출, skill loading",
        "done": "dispatch 프롬프트 댓글이 생성되면 성공",
    }
    assert "[AI Relay Dispatch]\nstatus: WORKING" in body
    assert "Dispatch prompt:" in body
    assert "Current agent: codex" in body
    assert "Done condition: dispatch 프롬프트 댓글이 생성되면 성공" in body


def test_handle_issue_comment_event_posts_verify_from_latest_hidden_state(tmp_path: Path) -> None:
    event_path = write_event(tmp_path, "/relay verify", issue_number=42)
    hidden_comment = ai_relay_harness.format_hidden_state_comment(
        {
            "status": "WORKING",
            "current_agent": "claude",
            "next_agent": "codex",
            "round": 0,
            "goal": "/relay verify 구현",
            "scope": "자기검증 프롬프트 생성",
            "out_of_scope": "실제 AI 호출, skill loading",
            "done": "verify 댓글이 생성되면 성공",
        }
    )
    posted_comments: list[tuple[str, int, str, str]] = []

    def record_comment(repository: str, issue_number: int, body: str, token: str) -> None:
        posted_comments.append((repository, issue_number, body, token))

    def list_comments(repository: str, issue_number: int, token: str) -> Sequence[Mapping[str, object]]:
        return [{"body": "old"}, {"body": hidden_comment}]

    posted = ai_relay_harness.handle_issue_comment_event(
        tmp_path,
        event_path,
        "owner/repo",
        "token",
        post_comment=record_comment,
        list_comments=list_comments,
    )

    assert posted is True
    assert len(posted_comments) == 1
    repository, issue_number, body, token = posted_comments[0]
    assert (repository, issue_number, token) == ("owner/repo", 42, "token")
    assert ai_relay_harness.extract_hidden_state(body) == {
        "status": "WORKING",
        "current_agent": "claude",
        "next_agent": "codex",
        "round": 0,
        "goal": "/relay verify 구현",
        "scope": "자기검증 프롬프트 생성",
        "out_of_scope": "실제 AI 호출, skill loading",
        "done": "verify 댓글이 생성되면 성공",
    }
    assert "[AI Relay Verify]\nstatus: WORKING" in body
    assert "current_agent: claude" in body
    assert "next_agent: codex" in body
    assert "goal: /relay verify 구현" in body
    assert "Self-verification prompt:" in body
    assert "Report PASS or BLOCK" in body


def test_handle_issue_comment_event_posts_verify_ready_fallback_without_hidden_state(tmp_path: Path) -> None:
    event_path = write_event(tmp_path, "/relay verify", issue_number=42)
    posted_comments: list[tuple[str, int, str, str]] = []

    def record_comment(repository: str, issue_number: int, body: str, token: str) -> None:
        posted_comments.append((repository, issue_number, body, token))

    def list_comments(repository: str, issue_number: int, token: str) -> Sequence[Mapping[str, object]]:
        return []

    posted = ai_relay_harness.handle_issue_comment_event(
        tmp_path,
        event_path,
        "owner/repo",
        "token",
        post_comment=record_comment,
        list_comments=list_comments,
    )

    assert posted is True
    assert len(posted_comments) == 1
    body = posted_comments[0][2]
    assert ai_relay_harness.extract_hidden_state(body) == {
        "status": "READY",
        "current_agent": "none",
        "next_agent": "none",
        "round": 0,
        "requires_human": False,
    }
    assert "[AI Relay Verify]" in body
    assert "status: READY" in body
    assert "Self-verification prompt:" in body


def test_handle_issue_comment_event_ignores_verify_variant(tmp_path: Path) -> None:
    event_path = write_event(tmp_path, "/relay verify now")
    posted_comments: list[tuple[str, int, str, str]] = []

    def record_comment(repository: str, issue_number: int, body: str, token: str) -> None:
        posted_comments.append((repository, issue_number, body, token))

    posted = ai_relay_harness.handle_issue_comment_event(
        tmp_path,
        event_path,
        "owner/repo",
        "token",
        post_comment=record_comment,
    )

    assert posted is False
    assert posted_comments == []


def test_handle_issue_comment_event_ignores_relay_handoff(tmp_path: Path) -> None:
    event_path = write_event(tmp_path, "/relay handoff")
    posted_comments: list[tuple[str, int, str, str]] = []

    def record_comment(repository: str, issue_number: int, body: str, token: str) -> None:
        posted_comments.append((repository, issue_number, body, token))

    posted = ai_relay_harness.handle_issue_comment_event(
        tmp_path,
        event_path,
        "owner/repo",
        "token",
        post_comment=record_comment,
    )

    assert posted is False
    assert posted_comments == []


def test_workflow_checks_out_pr_head_before_reading_state() -> None:
    workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ai-relay.yml").read_text(
        encoding="utf-8"
    )

    assert "workflow_run" not in workflow
    assert "uses: actions/github-script@v7" in workflow
    assert "github.rest.pulls.get" in workflow
    assert "pull.head.repo.full_name" in workflow
    assert "pull.head.sha" in workflow
    assert "repository: ${{ steps.checkout-target.outputs.repository }}" in workflow
    assert "ref: ${{ steps.checkout-target.outputs.ref }}" in workflow
