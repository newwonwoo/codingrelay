# AI Baton

## Task Goal
- Implement `/relay dispatch` prompt generation from the latest hidden relay state and latest hidden relay plan.

## Current Agent
- codex

## Next Agent
- claude

## Work Completed
- Added exact `/relay dispatch` command matching.
- Added dispatch prompt/comment rendering that targets the current agent by name without `@claude` or `@codex` mentions.
- Wired `/relay dispatch` into the existing issue/PR comment handler so it reads latest hidden state and plan before posting the prompt.
- Added an `issue_comment_dispatch.json` fixture and pytest coverage for command matching, prompt rendering, state/plan integration, and variant command rejection.
- Re-ran required local verification commands.

## Changed Files
- .github/scripts/ai_relay_harness.py
- tests/test_ai_relay_harness.py
- tests/fixtures/issue_comment_dispatch.json
- AI_BATON.md
- AI_EVIDENCE.md
- AI_RISKS.md
- AI_DECISIONS.md

## Decision Reasons
- Keep dispatch as a pre-call prompt generation step only, matching the requested boundary.
- Reuse hidden JSON state and plan as the source of truth to minimize changes and avoid workflow edits.

## Evidence
- Test: `python -m pytest tests/test_ai_relay_harness.py -q`
- Build: Not applicable for this Python harness change.
- Lint: `python -m py_compile .github/scripts/ai_relay_harness.py`
- Typecheck: Not applicable for this Python standard-library script.
- Manual Check: Confirmed dispatch output contains no `@codex` or `@claude` mention strings in tests.

## Known Risks
- `/relay dispatch` only posts a prompt; it does not invoke an agent or load skills.
- Dispatch prompt quality depends on the latest hidden plan fields being complete.

## Six-Month Failure Risks
- If plan/state hidden comment formats change, dispatch may render incomplete prompts until fixtures are updated.
- Users may expect `/relay dispatch` to auto-call agents; this step intentionally does not.

## Receiver Compatibility Risks
- Next Agent may assume dispatch automation exists; only prompt generation exists.

## Do Not Touch
- Do not add live `@codex`/`@claude` invocation, skill loading, dashboards, merge automation, or multi-repository orchestration for this step.

## Next Actions
- Review the dispatch prompt wording in a real PR comment dry-run.
- If approved, a later step can add explicit opt-in agent mention behavior.

## Handoff Status
PASS
