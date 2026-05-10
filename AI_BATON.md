# AI Baton

## Task Goal
- Restore `ai_relay_harness.py` and `test_ai_relay_harness.py` to a working state after PR #16's merge conflict left both files with SyntaxError-level corruption (duplicated function definitions and stray `return` statements).

## Current Agent
- claude

## Next Agent
- codex

## Work Completed
- Diagnosed: latest `main` (`4e02d28`, PR #16 merge) left `.github/scripts/ai_relay_harness.py` and `tests/test_ai_relay_harness.py` un-importable. Two competing API designs were spliced together by hand without resolving the duplication.
- Confirmed two clean predecessor designs in git history:
  - `f29e3c2` "Add relay dispatch prompt command" — separate `AI_RELAY_PLAN` hidden marker, `format_dispatch_comment(state, plan)`. 26 tests pass.
  - `0c6e662` "Add relay dry-run fixture tests" — single `AI_RELAY_STATE` marker, no separate plan. 23 tests pass.
- Decision recorded in `AI_DECISIONS.md`: adopt `f29e3c2` as the base because `AI_BATON.md`/`AI_DECISIONS.md`/`AI_EVIDENCE.md` already document that design as the most recent intent and the dispatch fixture (`issue_comment_dispatch.json`) is already on disk.
- Restored both files to the `f29e3c2` revision verbatim. No new code authored in this round — smallest safe change.
- Re-ran `python3 -m py_compile` and `python3 -m pytest -q`. Both clean. 26 tests pass in 0.20s.

## Changed Files
- `.github/scripts/ai_relay_harness.py`
- `tests/test_ai_relay_harness.py`
- `AI_BATON.md`
- `AI_EVIDENCE.md`
- `AI_RISKS.md`
- `AI_DECISIONS.md`
- `AI_RELAY_STATE.json`

## Decision Reasons
- Smallest safe change: restore the two clean files instead of hand-merging two conflicting designs in one round.
- `f29e3c2` was already the most-documented intent across baton/decisions/evidence files, and its design (separate `AI_RELAY_PLAN` marker) matches the existing fixture set.
- The dry-run CLI from `0c6e662` is intentionally **not** absorbed in this round to keep the diff small and reviewable. It can be re-added cleanly on top of this base in a follow-up.

## Evidence
- Test: `python3 -m pytest -q` — 26 passed in 0.20s
- Build: Not applicable (Python harness, no build).
- Lint: `python3 -m py_compile .github/scripts/ai_relay_harness.py` — exit 0
- Typecheck: Not applicable for stdlib-only script.
- Manual Check: Diffed restored files against `f29e3c2`; verified no merge conflict markers, no duplicated function defs.

## Known Risks
- The dry-run CLI (`--dry-run`, `--comments-path`, `--summary`) and its 2 tests from `0c6e662` are **not** present in this restored state. Anyone relying on local dry-run will see those flags missing.
- `AI_EVIDENCE.md`'s 2026-05-09 evidence section claims local `--dry-run` was exercised — that path no longer exists post-restoration. Left in place as historical record; new evidence section makes the current state explicit.

## Six-Month Failure Risks
- If a future PR resolves a conflict by hand again without running `python3 -m py_compile` locally, the same class of failure can recur silently because the GitHub Actions workflow only runs the harness inside a workflow_dispatch path — there is no required PR check that imports the harness module.
- Fix: add a CI step that runs `python3 -m py_compile .github/scripts/ai_relay_harness.py` and `python3 -m pytest -q` on every PR before merge.

## Receiver Compatibility Risks
- Codex may want to immediately re-add the `--dry-run` CLI from `0c6e662`. That work is intentionally deferred. If receiver picks it up, do it as a single small additive change — do not also rename `format_dispatch_comment` or alter the plan-marker design.
- The test file uses `importlib.util` to load the harness directly from `.github/scripts/`, so adding any top-level import-time side effects to the harness will break tests.

## Do Not Touch
- Do not collapse `AI_RELAY_STATE` and `AI_RELAY_PLAN` into a single hidden marker. The current design and all `*.md` evidence assume they are separate.
- Do not add `@claude` / `@codex` mention strings to dispatch output. Tests assert their absence.
- Do not add live AI provider calls, skill loading, merge automation, dashboards, or kakao notification — outside V1 MVP boundary per `AGENTS.md` and `ai_relay_orchestrator_v1.md` §6.

## Next Actions
- Optional follow-up (next round): re-introduce the `--dry-run`, `--comments-path`, `--summary` CLI from `0c6e662` plus the 2 dry-run pytest cases. Keep it additive — do not modify existing public function signatures.
- Optional follow-up: add a `python3 -m pytest` step to `.github/workflows/ai-relay.yml` so a future bad merge fails the PR check immediately.
- Push branch `claude/ai-relay-development-XEceg` to origin so codex can review the recovery.

## Handoff Status
PASS
