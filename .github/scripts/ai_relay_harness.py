#!/usr/bin/env python3
"""Minimal V1 AI Relay GitHub Actions harness.

Phase 1 intentionally validates repository relay files and writes an Actions
summary. Command parsing, comment posting, full state transitions, and Kakao
sending are later MVP phases described in docs/ai-relay-v1-implementation-plan.md.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_FILES = [
    "AI_RELAY_CONTRACT.md",
    "AI_RELAY_STATE.json",
    "AI_BATON.md",
    "AI_EVIDENCE.md",
    "AI_RISKS.md",
]

REQUIRED_BATON_SECTIONS = [
    "Task Goal",
    "Current Agent",
    "Next Agent",
    "Work Completed",
    "Changed Files",
    "Decision Reasons",
    "Evidence",
    "Known Risks",
    "Six-Month Failure Risks",
    "Receiver Compatibility Risks",
    "Do Not Touch",
    "Next Actions",
    "Handoff Status",
]

VALID_AGENTS = {"claude", "codex"}
VALID_STATUSES = {
    "READY",
    "WORKING",
    "SELF_VERIFYING",
    "NEEDS_SELF_FIX",
    "EVIDENCE_CHECKING",
    "READY_FOR_HANDOFF",
    "RECEIVER_REVIEWING",
    "ACCEPTED_BY_RECEIVER",
    "REJECTED_BY_RECEIVER",
    "WORKING_BY_NEXT_AGENT",
    "BLOCKED",
    "DONE",
    "HUMAN_REQUIRED",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def read_event(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return load_json(path)


def check_required_files(root: Path) -> list[str]:
    missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]
    return [f"Missing required file: {name}" for name in missing]


def check_state(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    current_agent = state.get("current_agent")
    next_agent = state.get("next_agent")
    status = state.get("status")

    if current_agent not in VALID_AGENTS:
        errors.append("AI_RELAY_STATE.json has invalid current_agent")
    if next_agent not in VALID_AGENTS:
        errors.append("AI_RELAY_STATE.json has invalid next_agent")
    if current_agent == next_agent:
        errors.append("AI_RELAY_STATE.json current_agent and next_agent must differ")
    if status not in VALID_STATUSES:
        errors.append("AI_RELAY_STATE.json has invalid status")

    for key in ("round", "self_fix_count", "receiver_reject_count", "max_rounds", "max_self_fix", "max_receiver_reject"):
        if not isinstance(state.get(key), int):
            errors.append(f"AI_RELAY_STATE.json {key} must be an integer")

    if not isinstance(state.get("requires_human"), bool):
        errors.append("AI_RELAY_STATE.json requires_human must be a boolean")

    return errors


def check_baton(root: Path) -> list[str]:
    baton = (root / "AI_BATON.md").read_text(encoding="utf-8")
    missing = [section for section in REQUIRED_BATON_SECTIONS if f"## {section}" not in baton]
    return [f"AI_BATON.md missing section: {section}" for section in missing]


def infer_event_target(event: dict[str, Any]) -> str:
    if "issue" in event:
        issue = event["issue"]
        if isinstance(issue, dict) and "number" in issue:
            return f"issue #{issue['number']}"
    if "pull_request" in event:
        pull_request = event["pull_request"]
        if isinstance(pull_request, dict) and "number" in pull_request:
            return f"pull request #{pull_request['number']}"
    return "repository"


def render_summary(event_name: str, event_target: str, state: dict[str, Any], errors: list[str]) -> str:
    lines = [
        "# AI Relay Harness",
        "",
        f"- Event: `{event_name}`",
        f"- Target: {event_target}",
        f"- Status: `{state.get('status', 'unknown')}`",
        f"- Current Agent: `{state.get('current_agent', 'unknown')}`",
        f"- Next Agent: `{state.get('next_agent', 'unknown')}`",
        f"- Handoff Status: `{state.get('handoff_status', 'unknown')}`",
        "",
    ]

    if errors:
        lines.append("## Validation Errors")
        lines.extend(f"- {error}" for error in errors)
    else:
        lines.append("## Validation")
        lines.append("- Relay skeleton validation passed.")
        lines.append("- Phase 1 harness did not post comments or send Kakao notifications.")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the minimal AI Relay V1 harness.")
    parser.add_argument("--repo-root", default=".", help="Repository root path.")
    parser.add_argument("--event-name", default="workflow_dispatch", help="GitHub event name.")
    parser.add_argument("--event-path", default=None, help="Path to GitHub event payload JSON.")
    parser.add_argument("--summary", default=None, help="Path to GitHub step summary file.")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    event = read_event(Path(args.event_path) if args.event_path else None)

    errors = check_required_files(root)
    state: dict[str, Any] = {}
    if not errors:
        try:
            state = load_json(root / "AI_RELAY_STATE.json")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"Unable to load AI_RELAY_STATE.json: {exc}")

    if state:
        errors.extend(check_state(state))

    if (root / "AI_BATON.md").is_file():
        errors.extend(check_baton(root))

    summary = render_summary(args.event_name, infer_event_target(event), state, errors)
    if args.summary:
        Path(args.summary).write_text(summary, encoding="utf-8")
    print(summary)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
