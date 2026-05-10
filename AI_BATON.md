# AI Baton

## Task Goal
- Implement `/relay dispatch` prompt generation from the latest hidden relay state and latest hidden relay plan.
- Implement relay dispatch support for generating a work prompt from the current relay state and plan.

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
- Added `/relay plan` parsing so goal, scope, out-of-scope, and done fields are overlaid onto the latest hidden relay state.
- Added `/relay dispatch` handling that reads the latest hidden state/plan and posts a dispatch prompt comment without invoking any AI provider or loading skills.
- Added regression tests for plan/dispatch command matching, state formatting, and issue-comment handling.
- Renamed the workflow run step to reflect that the harness now handles multiple relay commands.
- Updated relay evidence, risks, decisions, and baton files for this work.

## Changed Files
- .github/scripts/ai_relay_harness.py
- tests/test_ai_relay_harness.py
- tests/fixtures/issue_comment_dispatch.json
- .github/workflows/ai-relay.yml
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
- Keep dispatch as prompt rendering only, matching the MVP boundary and the requested out-of-scope limits.
- Preserve hidden comment state as the source of truth so dispatch can use the same PR-thread state model as status and verify.

## Evidence
- Test: `python3 -m pytest -q`
- Build: Not applicable for this Python harness change.
- Lint: `python3 -m py_compile .github/scripts/ai_relay_harness.py`
- Typecheck: Not applicable for this Python standard-library script.
- Manual Check: Verified tests cover `/relay plan` capture and `/relay dispatch` prompt generation from latest hidden state.

## Known Risks
- `/relay dispatch` only creates a prompt comment; it does not notify or invoke the named current agent.
- Plan parsing remains line-oriented and only supports single-line values for each plan field.

## Six-Month Failure Risks
- GitHub comment ordering or pagination behavior could change, causing dispatch to read an older hidden state.
- Users may expect `/relay plan` to immediately dispatch work; the MVP separates plan capture from `/relay dispatch` prompt generation.

## Receiver Compatibility Risks
- Next Agent may assume provider mentions or skill loading were added; they remain intentionally out of scope.

## Do Not Touch
- Do not add live `@codex`/`@claude` invocation, skill loading, dashboards, merge automation, or multi-repository orchestration for this MVP step.

## Next Actions
- Consider adding `/relay dispatch` documentation examples if the command surface is documented in a future follow-up.
- Run the workflow on GitHub after pushing to verify live comment posting in the PR thread.

## Handoff Status
PASS
