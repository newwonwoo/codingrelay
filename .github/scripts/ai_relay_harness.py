#!/usr/bin/env python3
"""Respond to AI relay status commands from GitHub issue comments."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib import request

STATUS_COMMAND = "/relay status"
STATE_FILE = "AI_RELAY_STATE.json"

DEFAULT_RELAY_STATE: dict[str, Any] = {
    "status": "READY",
    "current_agent": "none",
    "next_agent": "none",
    "round": 0,
    "requires_human": False,
}


class RelayHarnessError(RuntimeError):
    """Raised when the relay harness cannot process a status request."""


def load_relay_state(repo_root: Path | str) -> dict[str, Any]:
    """Read AI_RELAY_STATE.json, or return the default READY state if absent."""
    state_path = Path(repo_root) / STATE_FILE
    if not state_path.is_file():
        return dict(DEFAULT_RELAY_STATE)

    state = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise RelayHarnessError(f"{STATE_FILE} must contain a JSON object.")
    return {**DEFAULT_RELAY_STATE, **state}


def format_status_value(value: Any) -> str:
    """Format values for stable status comments."""
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def format_status_response(state: Mapping[str, Any]) -> str:
    """Format the relay status response body."""
    merged_state = {**DEFAULT_RELAY_STATE, **state}
    return "\n".join(
        [
            "[AI Relay Status]",
            f"status: {merged_state['status']}",
            f"current_agent: {merged_state['current_agent']}",
            f"next_agent: {merged_state['next_agent']}",
            f"round: {merged_state['round']}",
            f"requires_human: {format_status_value(merged_state['requires_human'])}",
        ]
    )


def load_github_event(event_path: Path | str) -> dict[str, Any]:
    """Load a GitHub Actions event payload."""
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    if not isinstance(event, dict):
        raise RelayHarnessError("GitHub event payload must contain a JSON object.")
    return event


def is_relay_status_comment(event: Mapping[str, Any]) -> bool:
    """Return True only when the comment body exactly matches /relay status."""
    comment = event.get("comment")
    if not isinstance(comment, Mapping):
        return False
    return comment.get("body") == STATUS_COMMAND


def get_issue_number(event: Mapping[str, Any]) -> int:
    """Return the issue number shared by Issue and PR comment threads."""
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
    """Post a GitHub Issue/PR thread comment using GITHUB_TOKEN."""
    url = f"{api_url.rstrip('/')}/repos/{repository}/issues/{issue_number}/comments"
    payload = json.dumps({"body": body}).encode("utf-8")
    github_request = request.Request(
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
    with request.urlopen(github_request) as response:
        response.read()


def handle_issue_comment_event(
    repo_root: Path | str,
    event_path: Path | str,
    repository: str,
    token: str,
    post_comment: Callable[[str, int, str, str], None] = post_issue_comment,
) -> bool:
    """Post relay status for an exact /relay status issue_comment event.

    Returns False for all other comments. `/relay start` is intentionally not
    implemented in V1.
    """
    event = load_github_event(event_path)
    if not is_relay_status_comment(event):
        return False

    issue_number = get_issue_number(event)
    state = load_relay_state(repo_root)
    post_comment(repository, issue_number, format_status_response(state), token)
    return True


def main(argv: Sequence[str] | None = None) -> int:
    """Handle the current GitHub issue_comment event."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "repo_root",
        nargs="?",
        default=Path.cwd(),
        type=Path,
        help="Repository root containing AI_RELAY_STATE.json. Defaults to the current directory.",
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
        help="GitHub token used to post status comments. Defaults to GITHUB_TOKEN.",
    )
    args = parser.parse_args(argv)

    try:
        if args.event_path is None:
            raise RelayHarnessError("GITHUB_EVENT_PATH is required.")

        event = load_github_event(args.event_path)
        if not is_relay_status_comment(event):
            print("No /relay status command found.")
            return 0

        if not args.repository:
            raise RelayHarnessError("GITHUB_REPOSITORY is required.")
        if not args.token:
            raise RelayHarnessError("GITHUB_TOKEN is required.")

        issue_number = get_issue_number(event)
        state = load_relay_state(args.repo_root)
        post_issue_comment(args.repository, issue_number, format_status_response(state), args.token)
    except (OSError, json.JSONDecodeError, RelayHarnessError) as exc:
        print(str(exc))
        return 1

    print("AI relay status comment posted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
