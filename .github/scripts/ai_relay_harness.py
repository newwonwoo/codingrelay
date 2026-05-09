#!/usr/bin/env python3
"""Validation and GitHub issue-comment handling for the AI relay repository."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence
from urllib import request


REQUIRED_FILES = [
    "AGENTS.md",
    "AI_RELAY_CONTRACT.md",
    "AI_RELAY_STATE.json",
    "AI_BATON.md",
    "AI_DECISIONS.md",
    "AI_EVIDENCE.md",
    "AI_RISKS.md",
]

DEFAULT_RELAY_STATE = {
    "status": "READY",
    "current_agent": "none",
    "next_agent": "none",
    "round": 0,
    "requires_human": False,
}

STATUS_COMMAND = "/relay status"


class RelayHarnessError(RuntimeError):
    """Raised when the relay harness validation fails."""


def find_missing_required_files(
    repo_root: Path | str,
    required_files: Iterable[str] = REQUIRED_FILES,
) -> list[str]:
    """Return required root files that do not exist under ``repo_root``."""
    root = Path(repo_root)
    return [file_name for file_name in required_files if not (root / file_name).is_file()]


def validate_required_files(
    repo_root: Path | str,
    required_files: Sequence[str] = REQUIRED_FILES,
) -> None:
    """Validate that all required AI relay files exist at the repository root."""
    missing_files = find_missing_required_files(repo_root, required_files)
    if missing_files:
        raise RelayHarnessError(f"Missing required file: {missing_files[0]}")


def load_relay_state(repo_root: Path | str) -> dict[str, Any]:
    """Load AI_RELAY_STATE.json, or use the V1 default READY state if absent."""
    state_path = Path(repo_root) / "AI_RELAY_STATE.json"
    if not state_path.is_file():
        return dict(DEFAULT_RELAY_STATE)

    state = json.loads(state_path.read_text(encoding="utf-8"))
    return {**DEFAULT_RELAY_STATE, **state}


def format_bool(value: Any) -> str:
    """Format booleans for the stable relay status comment body."""
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def format_status_response(state: Mapping[str, Any]) -> str:
    """Format the relay status response posted back to GitHub issues/PRs."""
    return "\n".join(
        [
            "[AI Relay Status]",
            f"status: {state['status']}",
            f"current_agent: {state['current_agent']}",
            f"next_agent: {state['next_agent']}",
            f"round: {state['round']}",
            f"requires_human: {format_bool(state['requires_human'])}",
        ]
    )


def load_github_event(event_path: Path | str) -> dict[str, Any]:
    """Load the GitHub Actions event payload."""
    return json.loads(Path(event_path).read_text(encoding="utf-8"))


def is_relay_status_comment(event: Mapping[str, Any]) -> bool:
    """Return whether an issue_comment event contains the V1 status command."""
    if "issue" not in event:
        return False
    comment = event.get("comment")
    if not isinstance(comment, Mapping):
        return False
    return str(comment.get("body", "")).strip() == STATUS_COMMAND


def get_issue_number(event: Mapping[str, Any]) -> int:
    """Return the issue number for issue comments and PR comments alike."""
    issue = event.get("issue")
    if not isinstance(issue, Mapping) or "number" not in issue:
        raise RelayHarnessError("Missing issue number in GitHub event payload.")
    return int(issue["number"])


def post_issue_comment(
    repository: str,
    issue_number: int,
    body: str,
    token: str,
    api_url: str = "https://api.github.com",
) -> None:
    """Post a GitHub Issue comment using GITHUB_TOKEN."""
    url = f"{api_url.rstrip('/')}/repos/{repository}/issues/{issue_number}/comments"
    payload = json.dumps({"body": body}).encode("utf-8")
    comment_request = request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with request.urlopen(comment_request) as response:
        response.read()


def handle_issue_comment_event(
    repo_root: Path | str,
    event_path: Path | str,
    repository: str,
    token: str,
    post_comment: Callable[[str, int, str, str], None] = post_issue_comment,
) -> bool:
    """Post relay status when an issue_comment event contains /relay status."""
    event = load_github_event(event_path)
    if not is_relay_status_comment(event):
        return False

    issue_number = get_issue_number(event)
    state = load_relay_state(repo_root)
    post_comment(repository, issue_number, format_status_response(state), token)
    return True


def main(argv: Sequence[str] | None = None) -> int:
    """Run relay validation or handle a GitHub issue_comment event."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "repo_root",
        nargs="?",
        default=Path.cwd(),
        type=Path,
        help="Repository root to validate or use for status. Defaults to the current directory.",
    )
    parser.add_argument(
        "--handle-issue-comment",
        action="store_true",
        help="Handle a GitHub issue_comment event and respond to /relay status.",
    )
    parser.add_argument(
        "--event-path",
        default=os.environ.get("GITHUB_EVENT_PATH"),
        type=Path,
        help="Path to the GitHub event payload. Defaults to GITHUB_EVENT_PATH.",
    )
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY"),
        help="GitHub owner/repo. Defaults to GITHUB_REPOSITORY.",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub token for posting comments. Defaults to GITHUB_TOKEN.",
    )
    args = parser.parse_args(argv)

    try:
        if args.handle_issue_comment:
            if args.event_path is None:
                raise RelayHarnessError("GITHUB_EVENT_PATH is required for issue_comment handling.")
            if not args.repository:
                raise RelayHarnessError("GITHUB_REPOSITORY is required for issue_comment handling.")
            if not args.token:
                raise RelayHarnessError("GITHUB_TOKEN is required for issue_comment handling.")
            posted = handle_issue_comment_event(
                args.repo_root,
                args.event_path,
                args.repository,
                args.token,
            )
            print("AI relay status comment posted." if posted else "No /relay status command found.")
            return 0

        validate_required_files(args.repo_root)
    except (OSError, json.JSONDecodeError, RelayHarnessError) as exc:
        print(str(exc))
        return 1

    print("AI relay required file validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
