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
HANDOFF_COMMAND = "/relay handoff"
PLAN_COMMAND = "/relay plan"
VERIFY_COMMAND = "/relay verify"
DISPATCH_COMMAND = "/relay dispatch"
ACCEPT_COMMAND = "/relay accept"
REJECT_COMMAND = "/relay reject"
STOP_COMMAND = "/relay stop"
FIX_COMMAND = "/relay fix"
STATE_FILE = "AI_RELAY_STATE.json"
STATE_COMMENT_MARKER = "AI_RELAY_STATE"
PLAN_COMMENT_MARKER = "AI_RELAY_PLAN"
BATON_FILE = "AI_BATON.md"
EVIDENCE_FILE = "AI_EVIDENCE.md"

BATON_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Task Goal",
    "Current Agent",
    "Next Agent",
    "Changed Files",
    "Evidence",
    "Handoff Status",
)
EVIDENCE_REQUIRED_SECTIONS: tuple[str, ...] = (
    "Commands Run",
    "Results",
    "Not Verified",
)

DEFAULT_RELAY_STATE: dict[str, Any] = {
    "status": "READY",
    "current_agent": "none",
    "next_agent": "none",
    "round": 0,
    "requires_human": False,
}

DEFAULT_LIMITS: dict[str, int] = {
    "max_rounds": 3,
    "max_self_fix": 2,
    "max_receiver_reject": 1,
}

DEFAULT_START_STATE: dict[str, Any] = {
    "status": "WORKING",
    "current_agent": "claude",
    "next_agent": "codex",
    "round": 0,
    "goal": "",
}

PLAN_DEFAULTS: dict[str, str] = {
    "goal": "",
    "scope": "",
    "out_of_scope": "",
    "done": "",
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


def merge_plan(plan: Mapping[str, Any] | None) -> dict[str, Any]:
    """Merge a stored relay plan with plan-display defaults."""
    if plan is None:
        return dict(PLAN_DEFAULTS)
    return {**PLAN_DEFAULTS, **dict(plan)}


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


def format_handoff_response(previous_agent: str, state: Mapping[str, Any]) -> str:
    """Format the human-readable relay handoff response body."""
    return "\n".join(
        [
            "[AI Relay Handoff]",
            f"status: {state['status']}",
            f"previous_agent: {previous_agent}",
            f"current_agent: {state['current_agent']}",
            f"next_agent: {state['next_agent']}",
            f"round: {state['round']}",
            f"goal: {state.get('goal', '')}",
        ]
    )


def format_plan_response(plan: Mapping[str, Any]) -> str:
    """Format the human-readable relay plan response body."""
    merged_plan = merge_plan(plan)
    return "\n".join(
        [
            "[AI Relay Plan]",
            f"goal: {merged_plan['goal']}",
            f"scope: {merged_plan['scope']}",
            f"out_of_scope: {merged_plan['out_of_scope']}",
            f"done: {merged_plan['done']}",
        ]
    )


def format_verify_prompt(state: Mapping[str, Any], plan: Mapping[str, Any] | None = None) -> str:
    """Build a self-verification prompt without calling an AI provider."""
    merged_plan = merge_plan(plan)
    return "\n".join(
        [
            "Self-verification prompt:",
            "You are the current relay agent. Verify your own completed work before handoff.",
            f"Goal: {merged_plan['goal']}",
            f"Scope: {merged_plan['scope']}",
            f"Out of scope: {merged_plan['out_of_scope']}",
            f"Done condition: {merged_plan['done']}",
            "Check:",
            "1. Confirm the implementation satisfies the goal and done condition.",
            "2. Confirm no out-of-scope AI calls, skill loading, or unrelated automation were added.",
            "3. Run relevant tests or explain any environment limitation.",
            "4. Report PASS or BLOCK with concise evidence and remaining risks.",
            "",
            "Relay state:",
            f"status: {state.get('status', '')}",
            f"current_agent: {state.get('current_agent', '')}",
            f"next_agent: {state.get('next_agent', '')}",
            f"round: {state.get('round', '')}",
        ]
    )


def format_verify_response(state: Mapping[str, Any], plan: Mapping[str, Any] | None = None) -> str:
    """Format the human-readable relay verify response body."""
    merged_state = merge_status_state(state)
    merged_plan = merge_plan(plan)
    return "\n".join(
        [
            "[AI Relay Verify]",
            f"status: {merged_state['status']}",
            f"current_agent: {merged_state['current_agent']}",
            f"next_agent: {merged_state['next_agent']}",
            f"round: {merged_state['round']}",
            f"goal: {merged_plan['goal']}",
            "",
            format_verify_prompt(merged_state, merged_plan),
        ]
    )


def format_dispatch_prompt(state: Mapping[str, Any], plan: Mapping[str, Any] | None = None) -> str:
    """Build a work prompt for the current relay agent without auto-calling it."""
    merged_state = merge_status_state(state)
    merged_plan = merge_plan(plan)
    return "\n".join(
        [
            "Dispatch prompt:",
            "You are the current relay agent. Continue the work using the relay state and plan below.",
            f"Target agent: {merged_state['current_agent']}",
            f"Status: {merged_state['status']}",
            f"Current agent: {merged_state['current_agent']}",
            f"Next agent: {merged_state['next_agent']}",
            f"Round: {merged_state['round']}",
            f"Goal: {merged_plan['goal']}",
            f"Scope: {merged_plan['scope']}",
            f"Out of scope: {merged_plan['out_of_scope']}",
            f"Done condition: {merged_plan['done']}",
            "Instructions:",
            "1. Read the relay contract and evidence files before changing code.",
            "2. Make the smallest safe change inside scope.",
            "3. Do not perform provider calls, skill loading, agent mentions, or unrelated automation.",
            "4. Run relevant tests or explain any environment limitation.",
            "5. Update relay evidence before handoff.",
        ]
    )


def format_dispatch_response(state: Mapping[str, Any], plan: Mapping[str, Any] | None = None) -> str:
    """Format the human-readable relay dispatch response body."""
    merged_state = merge_status_state(state)
    merged_plan = merge_plan(plan)
    return "\n".join(
        [
            "[AI Relay Dispatch]",
            f"status: {merged_state['status']}",
            f"current_agent: {merged_state['current_agent']}",
            f"next_agent: {merged_state['next_agent']}",
            f"round: {merged_state['round']}",
            f"goal: {merged_plan['goal']}",
            "",
            format_dispatch_prompt(merged_state, merged_plan),
        ]
    )


def format_hidden_json_comment(marker: str, payload: Mapping[str, Any]) -> str:
    """Serialize a hidden GitHub comment JSON block."""
    payload_json = json.dumps(dict(payload), ensure_ascii=False, indent=2)
    return f"<!-- {marker}\n{payload_json}\n-->"


def format_hidden_state_comment(state: Mapping[str, Any]) -> str:
    """Serialize relay state into a hidden GitHub comment block."""
    return format_hidden_json_comment(STATE_COMMENT_MARKER, state)


def format_hidden_plan_comment(plan: Mapping[str, Any]) -> str:
    """Serialize relay plan into a hidden GitHub comment block."""
    return format_hidden_json_comment(PLAN_COMMENT_MARKER, plan)


def format_start_comment(state: Mapping[str, Any]) -> str:
    """Format the combined hidden state and visible start response comment."""
    return f"{format_hidden_state_comment(state)}\n\n{format_start_response(state)}"


def format_handoff_comment(previous_agent: str, state: Mapping[str, Any]) -> str:
    """Format the combined hidden state and visible handoff response comment."""
    return f"{format_hidden_state_comment(state)}\n\n{format_handoff_response(previous_agent, state)}"


def format_plan_comment(plan: Mapping[str, Any]) -> str:
    """Format the combined hidden plan and visible plan response comment."""
    return f"{format_hidden_plan_comment(plan)}\n\n{format_plan_response(plan)}"


def format_gate_verdict(verdict: str, reasons: Sequence[str]) -> str:
    """Format the auto handoff-gate verdict block appended to /relay verify."""
    if verdict == "PASS" and not reasons:
        return "\n".join(
            [
                "Handoff gate: PASS",
                "All required AI_BATON.md and AI_EVIDENCE.md sections are filled.",
            ]
        )
    lines = ["Handoff gate: BLOCK", "Reasons:"]
    lines.extend(f"- {reason}" for reason in reasons)
    return "\n".join(lines)


def format_verify_comment(state: Mapping[str, Any], plan: Mapping[str, Any] | None = None) -> str:
    """Format the combined hidden state and visible verify response comment."""
    return f"{format_hidden_state_comment(state)}\n\n{format_verify_response(state, plan)}"


def format_dispatch_comment(state: Mapping[str, Any], plan: Mapping[str, Any] | None = None) -> str:
    """Format the combined hidden state and visible dispatch response comment."""
    return f"{format_hidden_state_comment(state)}\n\n{format_dispatch_response(state, plan)}"


def extract_hidden_json(comment_body: str, marker: str) -> dict[str, Any] | None:
    """Extract a hidden JSON object from a comment body for the requested marker."""
    start_marker = f"<!-- {marker}"
    start_index = comment_body.find(start_marker)
    if start_index == -1:
        return None

    json_start = start_index + len(start_marker)
    end_index = comment_body.find("-->", json_start)
    if end_index == -1:
        return None

    raw_payload = comment_body[json_start:end_index].strip()
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def extract_hidden_state(comment_body: str) -> dict[str, Any] | None:
    """Extract a hidden relay state JSON object from a comment body."""
    return extract_hidden_json(comment_body, STATE_COMMENT_MARKER)


def extract_hidden_plan(comment_body: str) -> dict[str, Any] | None:
    """Extract a hidden relay plan JSON object from a comment body."""
    return extract_hidden_json(comment_body, PLAN_COMMENT_MARKER)


def latest_hidden_payload(
    comments: Sequence[Mapping[str, Any]],
    extractor: Callable[[str], dict[str, Any] | None],
) -> dict[str, Any] | None:
    """Return the newest hidden payload from issue comments, if present."""
    for comment in reversed(comments):
        body = comment.get("body")
        if not isinstance(body, str):
            continue
        payload = extractor(body)
        if payload is not None:
            return payload
    return None


def latest_hidden_state(comments: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    """Return the newest hidden relay state from issue comments, if present."""
    return latest_hidden_payload(comments, extract_hidden_state)


def latest_hidden_plan(comments: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    """Return the newest hidden relay plan from issue comments, if present."""
    return latest_hidden_payload(comments, extract_hidden_plan)


def load_github_event(event_path: Path | str) -> dict[str, Any]:
    """Load a GitHub Actions event payload."""
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    if not isinstance(event, dict):
        raise RelayHarnessError("GitHub event payload must contain a JSON object.")
    return event


def load_comments_file(comments_path: Path | str) -> list[Mapping[str, Any]]:
    """Load a local fixture containing GitHub issue comments."""
    raw_comments = json.loads(Path(comments_path).read_text(encoding="utf-8"))
    if not isinstance(raw_comments, list):
        raise RelayHarnessError("Comments fixture must contain a JSON list.")
    return [comment for comment in raw_comments if isinstance(comment, Mapping)]


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


def is_relay_handoff_comment(event: Mapping[str, Any]) -> bool:
    """Return True when the first comment line exactly matches /relay handoff."""
    return get_command_line(event) == HANDOFF_COMMAND


def is_relay_plan_comment(event: Mapping[str, Any]) -> bool:
    """Return True when the first comment line exactly matches /relay plan."""
    return get_command_line(event) == PLAN_COMMAND


def is_relay_verify_comment(event: Mapping[str, Any]) -> bool:
    """Return True when the first comment line exactly matches /relay verify."""
    return get_command_line(event) == VERIFY_COMMAND


def is_relay_dispatch_comment(event: Mapping[str, Any]) -> bool:
    """Return True when the first comment line exactly matches /relay dispatch."""
    return get_command_line(event) == DISPATCH_COMMAND


def is_relay_accept_comment(event: Mapping[str, Any]) -> bool:
    """Return True when the first comment line exactly matches /relay accept."""
    return get_command_line(event) == ACCEPT_COMMAND


def is_relay_reject_comment(event: Mapping[str, Any]) -> bool:
    """Return True when the first comment line exactly matches /relay reject."""
    return get_command_line(event) == REJECT_COMMAND


def is_relay_stop_comment(event: Mapping[str, Any]) -> bool:
    """Return True when the first comment line exactly matches /relay stop."""
    return get_command_line(event) == STOP_COMMAND


def is_relay_fix_comment(event: Mapping[str, Any]) -> bool:
    """Return True when the first comment line exactly matches /relay fix."""
    return get_command_line(event) == FIX_COMMAND


def get_issue_number(event: Mapping[str, Any]) -> int:
    """Return the issue number shared by Issue and PR comment threads."""
    issue = event.get("issue")
    if not isinstance(issue, Mapping) or "number" not in issue:
        raise RelayHarnessError("Missing issue number in GitHub event payload.")
    return int(issue["number"])


def is_pull_request_comment_event(event: Mapping[str, Any]) -> bool:
    """Return True when an issue_comment payload belongs to a pull request thread."""
    issue = event.get("issue")
    return isinstance(issue, Mapping) and isinstance(issue.get("pull_request"), Mapping)


def parse_key_value_options(event: Mapping[str, Any], allowed_keys: set[str]) -> dict[str, str]:
    """Parse simple key/value options from relay comments after the command line."""
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
        if normalized_key in allowed_keys:
            options[normalized_key] = value.strip()
    return options


def parse_start_options(event: Mapping[str, Any]) -> dict[str, str]:
    """Parse start_agent, next_agent, and goal values from a start comment."""
    return parse_key_value_options(event, {"start_agent", "current_agent", "next_agent", "goal"})


def parse_plan_options(event: Mapping[str, Any]) -> dict[str, str]:
    """Parse goal, scope, out_of_scope, and done values from a plan comment."""
    return parse_key_value_options(event, {"goal", "scope", "out_of_scope", "done"})


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


def build_handoff_state(base_state: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    """Swap current/next agents and increment the relay round."""
    merged_state = merge_status_state(base_state)
    previous_agent = str(merged_state["current_agent"])
    next_round = _coerce_int(merged_state.get("round")) + 1
    swapped = {
        **dict(merged_state),
        "status": "WORKING",
        "current_agent": merged_state["next_agent"],
        "next_agent": merged_state["current_agent"],
        "round": next_round,
    }
    return previous_agent, enforce_limits(swapped)


def build_plan(event: Mapping[str, Any]) -> dict[str, Any]:
    """Build a relay plan from a /relay plan comment."""
    options = parse_plan_options(event)
    return {
        "goal": options.get("goal", ""),
        "scope": options.get("scope", ""),
        "out_of_scope": options.get("out_of_scope", ""),
        "done": options.get("done", ""),
    }


def parse_reason_option(event: Mapping[str, Any]) -> str:
    """Parse the reason value from a relay command comment, if present."""
    return parse_key_value_options(event, {"reason"}).get("reason", "")


def extract_section_content(markdown: str, section_title: str) -> str | None:
    """Return the trimmed content under a `## <section_title>` header, if present.

    Returns None when the section header is absent. Returns "" when the section
    exists but has no non-blank content before the next header or end of file.
    """
    lines = markdown.splitlines()
    target = f"## {section_title}"
    in_section = False
    collected: list[str] = []
    for line in lines:
        if line.strip() == target:
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            collected.append(line)
    if not in_section:
        return None
    content = "\n".join(collected).strip()
    return content


def section_is_filled(markdown: str, section_title: str) -> bool:
    """Return True when the section exists and has at least one non-placeholder line."""
    content = extract_section_content(markdown, section_title)
    if content is None or not content:
        return False
    placeholder_only = True
    for raw_line in content.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped in {"-", "*"}:
            continue
        placeholder_only = False
        break
    return not placeholder_only


def check_baton_required(repo_root: Path | str) -> list[str]:
    """Return a list of human-readable problems with AI_BATON.md, or [] when PASS."""
    baton_path = Path(repo_root) / BATON_FILE
    if not baton_path.is_file():
        return [f"{BATON_FILE} is missing."]
    content = baton_path.read_text(encoding="utf-8")
    problems: list[str] = []
    for section in BATON_REQUIRED_SECTIONS:
        if extract_section_content(content, section) is None:
            problems.append(f"{BATON_FILE} missing section '## {section}'.")
        elif not section_is_filled(content, section):
            problems.append(f"{BATON_FILE} section '## {section}' is empty.")
    handoff = extract_section_content(content, "Handoff Status")
    if handoff is not None:
        normalized = handoff.strip().splitlines()[0].strip() if handoff.strip() else ""
        allowed = {"PASS", "CONDITIONAL_PASS", "BLOCK"}
        if normalized and normalized not in allowed:
            problems.append(
                f"{BATON_FILE} 'Handoff Status' must be PASS, CONDITIONAL_PASS, or BLOCK; got '{normalized}'."
            )
    return problems


def check_evidence_required(repo_root: Path | str) -> list[str]:
    """Return a list of human-readable problems with AI_EVIDENCE.md, or [] when PASS."""
    evidence_path = Path(repo_root) / EVIDENCE_FILE
    if not evidence_path.is_file():
        return [f"{EVIDENCE_FILE} is missing."]
    content = evidence_path.read_text(encoding="utf-8")
    problems: list[str] = []
    for section in EVIDENCE_REQUIRED_SECTIONS:
        if extract_section_content(content, section) is None:
            problems.append(f"{EVIDENCE_FILE} missing section '## {section}'.")
        elif not section_is_filled(content, section):
            problems.append(f"{EVIDENCE_FILE} section '## {section}' is empty.")
    return problems


def evaluate_handoff_gate(repo_root: Path | str) -> tuple[str, list[str]]:
    """Return (verdict, reasons) where verdict is 'PASS' or 'BLOCK'."""
    reasons = check_baton_required(repo_root) + check_evidence_required(repo_root)
    return ("BLOCK" if reasons else "PASS"), reasons


def _coerce_int(value: Any, default: int = 0) -> int:
    """Tolerantly coerce a state field to int; fall back to default."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def evaluate_limit_breach(state: Mapping[str, Any]) -> list[str]:
    """Return human-readable reasons when round/self_fix/receiver_reject limits are exceeded."""
    reasons: list[str] = []
    rounds = _coerce_int(state.get("round"))
    max_rounds = _coerce_int(state.get("max_rounds"), DEFAULT_LIMITS["max_rounds"])
    self_fix = _coerce_int(state.get("self_fix_count"))
    max_self_fix = _coerce_int(state.get("max_self_fix"), DEFAULT_LIMITS["max_self_fix"])
    rejects = _coerce_int(state.get("receiver_reject_count"))
    max_rejects = _coerce_int(state.get("max_receiver_reject"), DEFAULT_LIMITS["max_receiver_reject"])
    if rounds > max_rounds:
        reasons.append(f"round {rounds} exceeded max_rounds {max_rounds}.")
    if self_fix > max_self_fix:
        reasons.append(f"self_fix_count {self_fix} exceeded max_self_fix {max_self_fix}.")
    if rejects > max_rejects:
        reasons.append(f"receiver_reject_count {rejects} exceeded max_receiver_reject {max_rejects}.")
    return reasons


def enforce_limits(state: Mapping[str, Any]) -> dict[str, Any]:
    """Promote state to HUMAN_REQUIRED when any relay limit is exceeded."""
    breaches = evaluate_limit_breach(state)
    if not breaches:
        return dict(state)
    return {
        **dict(state),
        "status": "HUMAN_REQUIRED",
        "requires_human": True,
    }


def format_human_required_response(state: Mapping[str, Any], reasons: Sequence[str]) -> str:
    """Format the human-readable HUMAN_REQUIRED response body."""
    merged_state = merge_status_state(state)
    lines = [
        "[AI Relay Human Required]",
        f"status: {merged_state['status']}",
        f"current_agent: {merged_state['current_agent']}",
        f"next_agent: {merged_state['next_agent']}",
        f"round: {merged_state['round']}",
        f"requires_human: {format_status_value(merged_state['requires_human'])}",
        "Reasons:",
    ]
    lines.extend(f"- {reason}" for reason in reasons)
    lines.extend(
        [
            "",
            "Action:",
            "1. A human reviewer must inspect AI_BATON.md, AI_EVIDENCE.md, and AI_RISKS.md.",
            "2. Decide whether to redirect the goal, lower the limits, or close the relay.",
            "3. No further /relay handoff or /relay accept will succeed until the human resolves this.",
        ]
    )
    return "\n".join(lines)


def format_human_required_comment(state: Mapping[str, Any], reasons: Sequence[str]) -> str:
    """Format the combined hidden state and visible HUMAN_REQUIRED response comment."""
    return f"{format_hidden_state_comment(state)}\n\n{format_human_required_response(state, reasons)}"


def build_accept_state(base_state: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    """Swap agents and increment round when the receiver accepts the baton."""
    return build_handoff_state(base_state)


def build_reject_state(base_state: Mapping[str, Any]) -> dict[str, Any]:
    """Keep current_agent and bump receiver_reject_count when the receiver rejects."""
    merged_state = merge_status_state(base_state)
    next_reject_count = _coerce_int(merged_state.get("receiver_reject_count")) + 1
    next_state = {
        **dict(merged_state),
        "status": "REJECTED_BY_RECEIVER",
        "receiver_reject_count": next_reject_count,
    }
    return enforce_limits(next_state)


def format_accept_response(previous_agent: str, state: Mapping[str, Any]) -> str:
    """Format the human-readable relay accept response body."""
    return "\n".join(
        [
            "[AI Relay Accepted]",
            f"status: {state['status']}",
            f"previous_agent: {previous_agent}",
            f"current_agent: {state['current_agent']}",
            f"next_agent: {state['next_agent']}",
            f"round: {state['round']}",
            f"goal: {state.get('goal', '')}",
        ]
    )


def format_reject_response(state: Mapping[str, Any], reason: str) -> str:
    """Format the human-readable relay reject response body."""
    return "\n".join(
        [
            "[AI Relay Rejected]",
            f"status: {state['status']}",
            f"current_agent: {state['current_agent']}",
            f"next_agent: {state['next_agent']}",
            f"round: {state['round']}",
            f"receiver_reject_count: {state.get('receiver_reject_count', 0)}",
            f"reason: {reason}",
            "",
            "Self-fix prompt:",
            "Your baton or evidence was rejected by the next agent.",
            "Do not hand off yet.",
            f"Reason: {reason or 'unspecified'}",
            "Required:",
            "1. Read AI_RELAY_CONTRACT.md, AI_BATON.md, AI_EVIDENCE.md, AI_RISKS.md.",
            "2. Address the rejection reason without expanding scope.",
            "3. Update AI_BATON.md, AI_EVIDENCE.md, AI_RISKS.md.",
            "4. Re-run /relay verify before another handoff attempt.",
        ]
    )


def format_accept_comment(previous_agent: str, state: Mapping[str, Any]) -> str:
    """Format the combined hidden state and visible accept response comment."""
    return f"{format_hidden_state_comment(state)}\n\n{format_accept_response(previous_agent, state)}"


def format_reject_comment(state: Mapping[str, Any], reason: str) -> str:
    """Format the combined hidden state and visible reject response comment."""
    return f"{format_hidden_state_comment(state)}\n\n{format_reject_response(state, reason)}"


def build_stop_state(base_state: Mapping[str, Any], reason: str) -> dict[str, Any]:
    """Mark the relay as stopped (DONE) by user request."""
    merged_state = merge_status_state(base_state)
    return {
        **dict(merged_state),
        "status": "DONE",
        "stop_reason": reason,
    }


def build_fix_state(base_state: Mapping[str, Any]) -> dict[str, Any]:
    """Mark the relay as needing self-fix and bump self_fix_count."""
    merged_state = merge_status_state(base_state)
    next_self_fix = _coerce_int(merged_state.get("self_fix_count")) + 1
    next_state = {
        **dict(merged_state),
        "status": "NEEDS_SELF_FIX",
        "self_fix_count": next_self_fix,
    }
    return enforce_limits(next_state)


def format_stop_response(state: Mapping[str, Any], reason: str) -> str:
    """Format the human-readable relay stop response body."""
    return "\n".join(
        [
            "[AI Relay Stopped]",
            f"status: {state['status']}",
            f"current_agent: {state['current_agent']}",
            f"next_agent: {state['next_agent']}",
            f"round: {state['round']}",
            f"reason: {reason}",
            "",
            "No further /relay handoff, /relay accept, or /relay reject is processed.",
            "Use /relay start to begin a new task.",
        ]
    )


def format_self_fix_prompt(state: Mapping[str, Any], reasons: Sequence[str]) -> str:
    """Build a self-fix prompt the current agent is expected to act on."""
    merged_state = merge_status_state(state)
    lines = [
        "Self-fix prompt:",
        "Your baton or evidence failed the pre-handoff gate.",
        "Do not hand off yet.",
        f"Target agent: {merged_state['current_agent']}",
        f"Status: {merged_state['status']}",
        f"Round: {merged_state['round']}",
        f"self_fix_count: {merged_state.get('self_fix_count', 0)}",
        "Block reasons:",
    ]
    if reasons:
        lines.extend(f"- {reason}" for reason in reasons)
    else:
        lines.append("- (no specific reason supplied — re-run /relay verify)")
    lines.extend(
        [
            "Required:",
            "1. Update code if needed.",
            "2. Update AI_BATON.md so all required sections are filled.",
            "3. Update AI_EVIDENCE.md with Commands Run, Results, and Not Verified.",
            "4. Update AI_RISKS.md with any new six-month failure risks.",
            "5. Set Handoff Status to PASS, CONDITIONAL_PASS, or BLOCK.",
            "6. Re-run /relay verify before any handoff attempt.",
        ]
    )
    return "\n".join(lines)


def format_fix_response(state: Mapping[str, Any], reasons: Sequence[str]) -> str:
    """Format the human-readable relay fix response body."""
    return "\n".join(
        [
            "[AI Relay Self-Fix]",
            f"status: {state['status']}",
            f"current_agent: {state['current_agent']}",
            f"next_agent: {state['next_agent']}",
            f"round: {state['round']}",
            f"self_fix_count: {state.get('self_fix_count', 0)}",
            "",
            format_self_fix_prompt(state, reasons),
        ]
    )


def format_stop_comment(state: Mapping[str, Any], reason: str) -> str:
    """Format the combined hidden state and visible stop response comment."""
    return f"{format_hidden_state_comment(state)}\n\n{format_stop_response(state, reason)}"


def format_fix_comment(state: Mapping[str, Any], reasons: Sequence[str]) -> str:
    """Format the combined hidden state and visible fix response comment."""
    return f"{format_hidden_state_comment(state)}\n\n{format_fix_response(state, reasons)}"


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
    """List Issue/PR thread comments so the latest hidden relay payloads can be read."""
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


def resolve_relay_state(
    repo_root: Path | str,
    comments: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Resolve raw relay state from hidden comments first, then file/default fallback."""
    state = latest_hidden_state(comments)
    if state is not None:
        return state
    return load_relay_state(repo_root)


def resolve_relay_plan(comments: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Resolve raw relay plan from hidden comments, or return an empty plan."""
    return merge_plan(latest_hidden_plan(comments))


def handle_issue_comment_event(
    repo_root: Path | str,
    event_path: Path | str,
    repository: str,
    token: str,
    post_comment: Callable[[str, int, str, str], None] = post_issue_comment,
    list_comments: Callable[[str, int, str], Sequence[Mapping[str, Any]]] = list_issue_comments,
) -> bool:
    """Handle exact relay command comments.

    Returns False for all other comments. AI provider calls, skill loading,
    agent-mention automation, and dispatch automation are intentionally not
    implemented.
    """
    event = load_github_event(event_path)
    is_status = is_relay_status_comment(event)
    is_start = is_relay_start_comment(event)
    is_handoff = is_relay_handoff_comment(event)
    is_plan = is_relay_plan_comment(event)
    is_verify = is_relay_verify_comment(event)
    is_dispatch = is_relay_dispatch_comment(event)
    is_accept = is_relay_accept_comment(event)
    is_reject = is_relay_reject_comment(event)
    is_stop = is_relay_stop_comment(event)
    is_fix = is_relay_fix_comment(event)
    if not (
        is_status
        or is_start
        or is_handoff
        or is_plan
        or is_verify
        or is_dispatch
        or is_accept
        or is_reject
        or is_stop
        or is_fix
    ):
        return False

    issue_number = get_issue_number(event)
    if is_start:
        state = build_start_state(event)
        post_comment(repository, issue_number, format_start_comment(state), token)
        return True

    comments = list_comments(repository, issue_number, token)

    if is_status:
        state = resolve_status_state(repo_root, comments)
        post_comment(repository, issue_number, format_status_response(state), token)
        return True

    resolved_state = resolve_relay_state(repo_root, comments)
    breaches = evaluate_limit_breach(resolved_state)
    is_locked = bool(breaches) or merge_status_state(resolved_state).get("requires_human") is True
    # /relay stop is always honored so a human can clear a HUMAN_REQUIRED state.
    if is_locked and not is_stop:
        locked_state = enforce_limits(resolved_state)
        post_comment(
            repository,
            issue_number,
            format_human_required_comment(locked_state, breaches or ["requires_human flag set."]),
            token,
        )
        return True

    if is_handoff:
        previous_agent, state = build_handoff_state(resolve_relay_state(repo_root, comments))
        post_comment(repository, issue_number, format_handoff_comment(previous_agent, state), token)
        return True

    if is_accept:
        previous_agent, state = build_accept_state(resolve_relay_state(repo_root, comments))
        post_comment(repository, issue_number, format_accept_comment(previous_agent, state), token)
        return True

    if is_reject:
        reason = parse_reason_option(event)
        state = build_reject_state(resolve_relay_state(repo_root, comments))
        post_comment(repository, issue_number, format_reject_comment(state, reason), token)
        return True

    if is_plan:
        plan = build_plan(event)
        post_comment(repository, issue_number, format_plan_comment(plan), token)
        return True

    if is_verify:
        state = resolve_relay_state(repo_root, comments)
        plan = resolve_relay_plan(comments)
        verdict, reasons = evaluate_handoff_gate(repo_root)
        verify_comment = format_verify_comment(state, plan)
        gate_block = format_gate_verdict(verdict, reasons)
        post_comment(repository, issue_number, f"{verify_comment}\n\n{gate_block}", token)
        return True

    if is_dispatch:
        state = resolve_relay_state(repo_root, comments)
        plan = resolve_relay_plan(comments)
        post_comment(repository, issue_number, format_dispatch_comment(state, plan), token)
        return True

    if is_stop:
        reason = parse_reason_option(event)
        state = build_stop_state(resolve_relay_state(repo_root, comments), reason)
        post_comment(repository, issue_number, format_stop_comment(state, reason), token)
        return True

    if is_fix:
        state = build_fix_state(resolve_relay_state(repo_root, comments))
        _, reasons = evaluate_handoff_gate(repo_root)
        post_comment(repository, issue_number, format_fix_comment(state, reasons), token)
        return True

    return False


def make_dry_run_post_comment(summary_path: Path | None = None) -> Callable[[str, int, str, str], None]:
    """Build a post_comment function that prints instead of calling GitHub."""

    def dry_run_post_comment(repository: str, issue_number: int, body: str, token: str) -> None:
        output = "\n".join(
            [
                "[AI Relay Dry Run]",
                f"repository: {repository}",
                f"issue_number: {issue_number}",
                "comment_body:",
                body,
            ]
        )
        print(output)
        if summary_path is not None:
            summary_path.write_text(output + "\n", encoding="utf-8")

    return dry_run_post_comment


def make_fixture_list_comments(comments: Sequence[Mapping[str, Any]]) -> Callable[[str, int, str], Sequence[Mapping[str, Any]]]:
    """Build a list_comments function backed by local fixture data."""

    def fixture_list_comments(repository: str, issue_number: int, token: str) -> Sequence[Mapping[str, Any]]:
        return comments

    return fixture_list_comments


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
        default=os.environ.get("GITHUB_REPOSITORY", "dry-run/repo"),
        help="GitHub owner/repo. Defaults to GITHUB_REPOSITORY, or dry-run/repo in dry-run mode.",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub token used to post relay comments. Defaults to GITHUB_TOKEN.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the comment that would be posted instead of calling the GitHub API.",
    )
    parser.add_argument(
        "--comments-path",
        type=Path,
        help="Optional JSON fixture containing existing issue comments for dry-run/local simulation.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        help="Optional path to write the dry-run comment body summary.",
    )
    args = parser.parse_args(argv)

    try:
        if args.event_path is None:
            raise RelayHarnessError("GITHUB_EVENT_PATH is required.")
        if not args.repository:
            raise RelayHarnessError("GITHUB_REPOSITORY is required.")
        if not args.dry_run and not args.token:
            raise RelayHarnessError("GITHUB_TOKEN is required unless --dry-run is used.")

        post_comment = post_issue_comment
        list_comments: Callable[[str, int, str], Sequence[Mapping[str, Any]]] = list_issue_comments
        token = args.token or ""
        if args.dry_run:
            post_comment = make_dry_run_post_comment(args.summary)
            comments = load_comments_file(args.comments_path) if args.comments_path else []
            list_comments = make_fixture_list_comments(comments)

        posted = handle_issue_comment_event(
            args.repo_root,
            args.event_path,
            args.repository,
            token,
            post_comment=post_comment,
            list_comments=list_comments,
        )
    except (OSError, json.JSONDecodeError, RelayHarnessError) as exc:
        print(str(exc))
        return 1

    print("AI relay comment posted." if posted else "No supported relay command found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
