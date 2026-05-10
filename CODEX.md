# Codex Relay Notes

Codex participates as an Agent role, not as a hard-coded owner.

Before acting, read:

- `AI_RELAY_CONTRACT.md`
- `AI_BATON.md`
- `AI_EVIDENCE.md`
- `AI_RISKS.md`

When acting as Receiving Agent, decide ACCEPT, ACCEPT_WITH_WARNINGS, or REJECT before modifying code. Reply with `/relay accept` or `/relay reject` (with `reason:` line).

## Relay Commands

See `CLAUDE.md` — the command surface is identical. Both agents share the same harness.

## Receiver Acceptance Checklist

1. Is the goal in `AI_BATON.md` clear?
2. Are changed files and reasons listed?
3. Is `AI_EVIDENCE.md` filled with Commands Run, Results, and Not Verified?
4. Are risks explicit in `AI_RISKS.md`?
5. Can you continue without guessing?

If any answer is no, post `/relay reject` with a single `reason:` line. The harness will keep the current agent and bump `receiver_reject_count`.
