#!/usr/bin/env python3
"""Respond to AI relay commands from GitHub issue comments."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib import parse, request

STATUS_COMMAND = "/relay status"
START_COMMAND = "/relay start"
STATE_FILE = "AI_RELAY_STATE.json"
STATE_COMMENT_MARKER = "AI_RELAY_STATE"

DEFAULT_RELAY_STATE: dict[str, Any] = {
    "status": "READY",
    "current_agent": "none",
    "next_agent": "none",
    "round": 0,
    "requires_human": False,
}

DEFAULT_START_STATE: dict[str, Any] = {
    "status": "WORKING",
    "current_agent": "claude",
    "next_agent": "codex",
    "round": 0,
    "goal": "",
}


class RelayHarnessError(RuntimeError):
    """Raised when the relay harness cannot process a relay request."""


def load_relay_state(repo_root: Path | str) -> dict[str, Any]:
    """Read AI_RELAY_STATE.json, or return the default READY state if absent."""
    state_path = Path(repo_root) / STATE_FILE
    if not state_path.is_file():
        return dict(DEFAULT_RELAY_STATE)

    state = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise RelayHarnessError(f"{STATE_FILE} must contain a JSON object.")
    return {**DEFAULT_RELAY_STATE, **state}


def merge_status_state(state: Mapping[str, Any]) -> dict[str, Any]:
    """Merge a stored relay state with status-display defaults."""
    return {**DEFAULT_RELAY_STATE, **state}


def format_status_value(value: Any) -> str:
    """Format values for stable relay comments."""
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def format_status_response(state: Mapping[str, Any]) -> str:
    """Format the relay status response body."""
    merged_state = merge_status_state(state)
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


def format_start_response(state: Mapping[str, Any]) -> str:
    """Format the human-readable relay start response body."""
    return "\n".join(
        [
            "[AI Relay Started]",
            f"status: {state['status']}",
            f"current_agent: {state['current_agent']}",
            f"next_agent: {state['next_agent']}",
            f"round: {state['round']}",
            f"goal: {state.get('goal', '')}",
        ]
    )


def format_hidden_state_comment(state: Mapping[str, Any]) -> str:
    """Serialize relay state into a hidden GitHub comment block."""
    state_json = json.dumps(dict(state), ensure_ascii=False, indent=2)
    return f"<!-- {STATE_COMMENT_MARKER}\n{state_json}\n-->"


def format_start_comment(state: Mapping[str, Any]) -> str:
    """Format the combined hidden state and visible start response comment."""
    return f"{format_hidden_state_comment(state)}\n\n{format_start_response(state)}"


def extract_hidden_state(comment_body: str) -> dict[str, Any] | None:
    """Extract a hidden relay state JSON object from a comment body."""
    start_marker = f"<!-- {STATE_COMMENT_MARKER}"
    start_index = comment_body.find(start_marker)
    if start_index == -1:
        return None

    json_start = start_index + len(start_marker)
    end_index = comment_body.find("-->", json_start)
    if end_index == -1:
        return None

    raw_state = comment_body[json_start:end_index].strip()
    try:
        state = json.loads(raw_state)
    except json.JSONDecodeError:
        return None
    if not isinstance(state, dict):
        return None
    return state


def latest_hidden_state(comments: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    """Return the newest hidden relay state from issue comments, if present."""
    for comment in reversed(comments):
        body = comment.get("body")
        if not isinstance(body, str):
            continue
        state = extract_hidden_state(body)
        if state is not None:
            return state
    return None


def load_github_event(event_path: Path | str) -> dict[str, Any]:
    """Load a GitHub Actions event payload."""
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    if not isinstance(event, dict):
        raise RelayHarnessError("GitHub event payload must contain a JSON object.")
    return event


def get_comment_body(event: Mapping[str, Any]) -> str | None:
    """Return the issue_comment body from an event payload."""
    comment = event.get("comment")
    if not isinstance(comment, Mapping):
        return None
    body = comment.get("body")
    if not isinstance(body, str):
        return None
    return body


def get_command_line(event: Mapping[str, Any]) -> str | None:
    """Return the first comment line used as the relay command."""
    body = get_comment_body(event)
    if body is None:
        return None
    return body.splitlines()[0] if body else ""


def is_relay_status_comment(event: Mapping[str, Any]) -> bool:
    """Return True only when the comment body exactly matches /relay status."""
    return get_comment_body(event) == STATUS_COMMAND


def is_relay_start_comment(event: Mapping[str, Any]) -> bool:
    """Return True when the first comment line exactly matches /relay start."""
    return get_command_line(event) == START_COMMAND


def get_issue_number(event: Mapping[str, Any]) -> int:
    """Return the issue number shared by Issue and PR comment threads."""
    issue = event.get("issue")
    if not isinstance(issue, Mapping) or "number" not in issue:
        raise RelayHarnessError("Missing issue number in GitHub event payload.")
    return int(issue["number"])


def parse_start_options(event: Mapping[str, Any]) -> dict[str, str]:
    """Parse start_agent, next_agent, and goal values from a start comment."""
    body = get_comment_body(event) or ""
    options: dict[str, str] = {}
    for line in body.splitlines()[1:]:
        stripped_line = line.strip()
        if not stripped_line:
            continue
        if ":" in stripped_line:
            key, value = stripped_line.split(":", 1)
        elif "=" in stripped_line:
            key, value = stripped_line.split("=", 1)
        else:
            continue
        normalized_key = key.strip().lower().replace("-", "_")
        if normalized_key in {"start_agent", "current_agent", "next_agent", "goal"}:
            options[normalized_key] = value.strip()
    return options


def build_start_state(event: Mapping[str, Any]) -> dict[str, Any]:
    """Build the initial WORKING relay state for a /relay start comment."""
    options = parse_start_options(event)
    current_agent = options.get("start_agent") or options.get("current_agent") or DEFAULT_START_STATE["current_agent"]
    next_agent = options.get("next_agent") or DEFAULT_START_STATE["next_agent"]
    goal = options.get("goal") or DEFAULT_START_STATE["goal"]
    return {
        "status": DEFAULT_START_STATE["status"],
        "current_agent": current_agent,
        "next_agent": next_agent,
        "round": DEFAULT_START_STATE["round"],
        "goal": goal,
    }


def github_api_request(
    url: str,
    token: str,
    method: str = "GET",
    data: bytes | None = None,
) -> Any:
    """Call the GitHub API and decode a JSON response."""
    github_request = request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with request.urlopen(github_request) as response:
        response_body = response.read()
    if not response_body:
        return None
    return json.loads(response_body.decode("utf-8"))


def list_issue_comments(
    repository: str,
    issue_number: int,
    token: str,
    api_url: str = "https://api.github.com",
) -> list[Mapping[str, Any]]:
    """List Issue/PR thread comments so the latest hidden relay state can be read."""
    comments: list[Mapping[str, Any]] = []
    page = 1
    while True:
        query = parse.urlencode({"per_page": 100, "page": page})
        url = f"{api_url.rstrip('/')}/repos/{repository}/issues/{issue_number}/comments?{query}"
        page_comments = github_api_request(url, token)
        if not isinstance(page_comments, list):
            raise RelayHarnessError("GitHub comments API returned an unexpected response.")
        comments.extend(comment for comment in page_comments if isinstance(comment, Mapping))
        if len(page_comments) < 100:
            return comments
        page += 1


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
    github_api_request(url, token, method="POST", data=payload)


def resolve_status_state(
    repo_root: Path | str,
    comments: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Resolve status from hidden comment state first, then file/default fallback."""
    state = latest_hidden_state(comments)
    if state is not None:
        return merge_status_state(state)
    return load_relay_state(repo_root)


def handle_issue_comment_event(
    repo_root: Path | str,
    event_path: Path | str,
    repository: str,
    token: str,
    post_comment: Callable[[str, int, str, str], None] = post_issue_comment,
    list_comments: Callable[[str, int, str], Sequence[Mapping[str, Any]]] = list_issue_comments,
) -> bool:
    """Handle exact /relay status and /relay start issue_comment events.

    Returns False for all other comments. `/relay handoff`, `@claude`, and
    `@codex` automation are intentionally not implemented in V1.
    """
    event = load_github_event(event_path)
    if not is_relay_status_comment(event) and not is_relay_start_comment(event):
        return False

    issue_number = get_issue_number(event)
    if is_relay_start_comment(event):
        state = build_start_state(event)
        post_comment(repository, issue_number, format_start_comment(state), token)
        return True

    comments = list_comments(repository, issue_number, token)
    state = resolve_status_state(repo_root, comments)
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
        help="GitHub token used to post relay comments. Defaults to GITHUB_TOKEN.",
    )
    args = parser.parse_args(argv)

    try:
        if args.event_path is None:
            raise RelayHarnessError("GITHUB_EVENT_PATH is required.")
        if not args.repository:
            raise RelayHarnessError("GITHUB_REPOSITORY is required.")
        if not args.token:
            raise RelayHarnessError("GITHUB_TOKEN is required.")

        posted = handle_issue_comment_event(args.repo_root, args.event_path, args.repository, args.token)
    except (OSError, json.JSONDecodeError, RelayHarnessError) as exc:
        print(str(exc))
        return 1

    print("AI relay comment posted." if posted else "No supported relay command found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
