# AI Evidence

## Commands Run
- `python3 -m py_compile .github/scripts/ai_relay_harness.py`
- `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/ai-relay.yml"); puts "workflow yaml parsed"'`
- `printf '{}' > /tmp/ai-relay-empty-event.json && python3 .github/scripts/ai_relay_harness.py --event-name workflow_dispatch --event-path /tmp/ai-relay-empty-event.json --summary /tmp/ai-relay-summary.md`

## Results
- Harness script compiles with Python 3.
- Workflow YAML parses successfully with Ruby Psych.
- Harness validates the relay skeleton and writes a summary for a `workflow_dispatch` event.

## Failed Tests
- None.

## Logs
- See the latest GitHub Actions run summary for harness output once the workflow runs in GitHub.

## Screenshots / Runtime Evidence
- Not applicable for this non-UI skeleton.

## Not Verified
- Live GitHub comment creation.
- Live Kakao notification delivery.
- Full state transitions beyond skeleton validation.


## 2026-05-09 Runtime Test Attempt

### Commands Run
- `python3 -m py_compile .github/scripts/ai_relay_harness.py`
- `printf '{}' > /tmp/ai-relay-empty-event.json`
- `python3 .github/scripts/ai_relay_harness.py --event-name workflow_dispatch --event-path /tmp/ai-relay-empty-event.json --summary /tmp/ai-relay-summary.md`
- `cat /tmp/ai-relay-summary.md`
- `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/ai-relay.yml"); puts "workflow yaml parsed"'`
- `gh --version || true`
- `gh auth status || true`
- `git remote -v`

### Results
- Python compile passed.
- Local `workflow_dispatch` harness execution passed and printed `Relay skeleton validation passed.`
- Summary file was written to `/tmp/ai-relay-summary.md`.
- Workflow YAML parsed successfully with Ruby Psych.
- Live GitHub workflow dispatch was not started from this container because `gh` is not installed and no git remote is configured.

### Failed Tests
- None for local validation.

### Logs
- Harness output showed `Status: READY`, `Current Agent: claude`, `Next Agent: codex`, and `Relay skeleton validation passed.`

### Screenshots / Runtime Evidence
- Not applicable for this non-UI local validation.

### Not Verified
- Live GitHub Actions `workflow_dispatch` execution from the GitHub UI/API.
- Pull request check execution after pushing to a remote branch.

## 2026-05-09 Workflow Trigger Fix

### Results
- workflow_run removed because no target workflow exists.

## 2026-05-10 Relay Dispatch Prompt Support

### Commands Run
- `python3 -m py_compile .github/scripts/ai_relay_harness.py`
- `python3 -m pytest -q`
- `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/ai-relay.yml"); puts "workflow yaml parsed"'`

### Results
- Harness script compiles with Python 3.
- Pytest suite passed with coverage for `/relay plan` parsing and `/relay dispatch` prompt comment generation.
- Workflow YAML parses successfully with Ruby Psych.

### Failed Tests
- None.

### Logs
- `25 passed in 0.06s`
- `workflow yaml parsed`

### Screenshots / Runtime Evidence
- Not applicable for this non-UI harness change.

### Not Verified
- Live GitHub comment creation for `/relay plan` or `/relay dispatch` after pushing to GitHub.

## 2026-05-10 V1 Stages 1-5

### Commands Run
- `python3 -m py_compile .github/scripts/ai_relay_harness.py`
- `python3 -m pytest -q`

### Results
- `py_compile` exit 0 at the end of every stage.
- `pytest -q` cumulative growth: 26 → 35 (Stage 1) → 47 (Stage 2) → 56 (Stage 3) → 65 (Stage 4) → 69 (Stage 5).
- Final run: `69 passed in 0.37s`.
- `test_repo_baton_and_evidence_pass_their_own_gate` is green, meaning this repo's own `AI_BATON.md` and `AI_EVIDENCE.md` clear the new automated handoff gate.

### Failed Tests
- None.

### Logs
- `69 passed in 0.37s`

### Screenshots / Runtime Evidence
- Not applicable for stdlib-only Python harness.

### Not Verified
- Live GitHub Actions execution of `.github/workflows/ai-relay-tests.yml` on a real PR (no `gh` CLI in this container).
- Live kakao delivery — `kakao_notify` only exercised via injected sender; real `urlopen` POST is not invoked from the test suite.
- Long-form fault injection for Risks 7-10; these remain documented but unfixed in this round.

## 2026-05-10 PR #16 Merge Conflict Recovery

### Commands Run
- `python3 -m py_compile .github/scripts/ai_relay_harness.py`
- `python3 -m pytest -q`
- `git show f29e3c2:.github/scripts/ai_relay_harness.py > .github/scripts/ai_relay_harness.py`
- `git show f29e3c2:tests/test_ai_relay_harness.py > tests/test_ai_relay_harness.py`

### Results
- Before recovery: harness file failed `py_compile` at line 163 (stray `return` outside any function, plus duplicated function definitions left by PR #16's bad merge resolution).
- After restoring both files from commit `f29e3c2`: `py_compile` exit 0, pytest reports `26 passed in 0.20s`.
- No other files modified for the recovery itself (state/baton/risks/decisions updates are bookkeeping per CLAUDE.md, not code changes).

### Failed Tests
- None after recovery.
- Before recovery: every test failed at module-import time with SyntaxError.

### Logs
- `26 passed in 0.20s`

### Screenshots / Runtime Evidence
- Not applicable for this Python harness change.

### Not Verified
- Live GitHub Actions run after pushing `claude/ai-relay-development-XEceg` (no `gh` CLI in this environment, as documented in earlier evidence sections).
- Whether codex's intended `0c6e662` dry-run CLI path needs to be re-added — explicitly deferred to next round.

## 2026-05-10 Relay Dispatch Command Support

### Commands Run
- `python -m pytest tests/test_ai_relay_harness.py -q`
- `python -m py_compile .github/scripts/ai_relay_harness.py`

### Results
- Pytest suite passed with coverage for `/relay dispatch` exact matching, latest hidden state/plan prompt rendering, and variant command rejection.
- Harness script compiles with Python.

### Failed Tests
- None.

### Logs
- `26 passed in 0.17s`

### Screenshots / Runtime Evidence
- Not applicable for this non-UI harness change.

### Not Verified
- Live GitHub comment creation for `/relay dispatch` after pushing to GitHub.
- Any live `@claude` or `@codex` invocation; intentionally not implemented.
