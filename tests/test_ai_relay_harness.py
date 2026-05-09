from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


HARNESS_PATH = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "ai_relay_harness.py"
SPEC = importlib.util.spec_from_file_location("ai_relay_harness", HARNESS_PATH)
ai_relay_harness = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ai_relay_harness)


def write_required_files(repo_root: Path) -> None:
    for file_name in ai_relay_harness.REQUIRED_FILES:
        (repo_root / file_name).write_text("placeholder\n", encoding="utf-8")


def write_issue_comment_event(repo_root: Path, body: str, issue_number: int = 7) -> Path:
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


def test_required_files_include_design_chapter_7_root_files() -> None:
    assert ai_relay_harness.REQUIRED_FILES == [
        "AGENTS.md",
        "AI_RELAY_CONTRACT.md",
        "AI_RELAY_STATE.json",
        "AI_BATON.md",
        "AI_DECISIONS.md",
        "AI_EVIDENCE.md",
        "AI_RISKS.md",
    ]


def test_missing_agents_reports_required_file_error(tmp_path: Path) -> None:
    write_required_files(tmp_path)
    (tmp_path / "AGENTS.md").unlink()

    with pytest.raises(ai_relay_harness.RelayHarnessError, match="Missing required file: AGENTS.md"):
        ai_relay_harness.validate_required_files(tmp_path)


def test_missing_ai_decisions_reports_required_file_error(tmp_path: Path) -> None:
    write_required_files(tmp_path)
    (tmp_path / "AI_DECISIONS.md").unlink()

    with pytest.raises(
        ai_relay_harness.RelayHarnessError,
        match="Missing required file: AI_DECISIONS.md",
    ):
        ai_relay_harness.validate_required_files(tmp_path)


def test_missing_state_file_uses_default_ready_status(tmp_path: Path) -> None:
    assert ai_relay_harness.load_relay_state(tmp_path) == {
        "status": "READY",
        "current_agent": "none",
        "next_agent": "none",
        "round": 0,
        "requires_human": False,
    }


def test_status_response_format_matches_v1_example() -> None:
    assert ai_relay_harness.format_status_response(ai_relay_harness.DEFAULT_RELAY_STATE) == (
        "[AI Relay Status]\n"
        "status: READY\n"
        "current_agent: none\n"
        "next_agent: none\n"
        "round: 0\n"
        "requires_human: false"
    )


def test_handle_issue_comment_posts_status_to_issue_number(tmp_path: Path) -> None:
    event_path = write_issue_comment_event(tmp_path, "/relay status", issue_number=42)
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
            "status: WORKING\n"
            "current_agent: codex\n"
            "next_agent: claude\n"
            "round: 2\n"
            "requires_human: true",
            "token",
        )
    ]


def test_handle_issue_comment_ignores_relay_start(tmp_path: Path) -> None:
    event_path = write_issue_comment_event(tmp_path, "/relay start")
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
