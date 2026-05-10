# Claude Relay Notes

Claude participates as an Agent role, not as a hard-coded owner.

Before acting, read:

- `AI_RELAY_CONTRACT.md`
- `AI_BATON.md`
- `AI_EVIDENCE.md`
- `AI_RISKS.md`

When acting as Current Agent, make the smallest safe change and update Baton, Evidence, and Risks before handoff.

## Relay Commands

The harness reads `issue_comment` events on issues and pull requests. Each command must be the **first line of the comment** and an **exact match** (no leading spaces, no trailing spaces, no extra arguments unless documented).

| Command | Effect |
|---|---|
| `/relay status` | Post the latest hidden state from this thread (or READY default). |
| `/relay start` | Begin a new relay. Optional `start_agent:`, `next_agent:`, `goal:` lines. |
| `/relay plan` | Capture `goal:`, `scope:`, `out_of_scope:`, `done:` into a hidden plan marker. |
| `/relay verify` | Render self-verification prompt and append the auto handoff gate verdict. |
| `/relay dispatch` | Render a work prompt for the current agent. No `@` mentions. |
| `/relay handoff` | Swap current/next agent and increment `round`. |
| `/relay accept` | Receiver accepts the baton; agents swap, `round++`. |
| `/relay reject` | Receiver rejects. Optional `reason:`. `receiver_reject_count++`, current agent stays. |
| `/relay fix` | Mark `NEEDS_SELF_FIX`, `self_fix_count++`. Embeds gate reasons as a self-fix prompt. |
| `/relay stop` | Mark `DONE`. Optional `reason:`. Always honored, even when locked. |

## Limits and HUMAN_REQUIRED

When `round`, `self_fix_count`, or `receiver_reject_count` exceeds its `max_*`, the harness automatically promotes the state to `HUMAN_REQUIRED` and silences every command except `/relay status` and `/relay stop`. Defaults: `max_rounds=3`, `max_self_fix=2`, `max_receiver_reject=1`. Override via `AI_RELAY_STATE.json`.

## Out of Scope (V1)

- Live `@claude` / `@codex` mentions — never injected by the harness
- Skill loading or AI provider calls — out of MVP boundary
- Auto-merge, dashboards, multi-repository orchestration
- Live kakao webhook delivery (the interface is in place; secret-backed delivery is opt-in)
