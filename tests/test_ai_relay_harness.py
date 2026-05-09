from __future__ import annotations

import importlib.util
import json
from pathlib import Path


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


def test_handle_issue_comment_event_posts_status_to_issue_number(tmp_path: Path) -> None:
    event_path = write_event(tmp_path, "/relay status", issue_number=42)
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


def test_handle_issue_comment_event_ignores_relay_start(tmp_path: Path) -> None:
    event_path = write_event(tmp_path, "/relay start")
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
