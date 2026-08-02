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

## 2026-05-10 Stage 8: Tragic-Failure Audit of Stages 6-7 → Risks 12-14 Landed

### Audit Approach
Applied orchestrator §13.2 six-month-failure prompt to every line changed in Stages 6-7 (373 diff lines) across 8 axes: hardcoding, missing tests, fragile deps, unclear state transitions, hidden coupling, poor logging, incomplete error handling, doc mismatch.

### Findings
- **Risk 12**: `kakao_notify` had no urlopen timeout → indefinite hang possible.
- **Risk 13**: `github_api_request` ignored `Retry-After` → wasted retries under throttling.
- **Risk 14**: `github_api_request` treated 403 as non-retryable, missing secondary rate limits.
- Documented but not fixed: `latest_hidden_payload` with mismatched fence markers (Risk H, too edge-case); non-idempotent POST retry can duplicate comments on partial network failure (Risk P, defer to server-side idempotency); `task_id` not carried across DONE→force restart (Risk V, feature-gap).

### Commands Run
- `python3 -m py_compile .github/scripts/ai_relay_harness.py`
- `python3 -m pytest -q`

### Results
- Risk 12: `kakao_notify` now passes `timeout=10` to `request.urlopen`.
- Risk 13: `github_api_request` honors `Retry-After` when parseable, `max(configured, header)`.
- Risk 14: `github_api_request` retries 403 when `x-ratelimit-remaining: 0`; other 403s stay non-retryable.
- Pytest cumulative: 85 → 90. Final run: `90 passed in 0.28s`.

### Failed Tests
- None.

### Logs
- `90 passed in 0.28s`

### Not Verified
- Live GitHub secondary rate limit path (can't induce in test).
- Live kakao webhook `timeout=10` behavior against real slow host.

## 2026-05-10 Stage 7: Risk 11 Fix (Kakao Failure Isolation)

### Commands Run
- `python3 -m py_compile .github/scripts/ai_relay_harness.py`
- `python3 -m pytest -q`

### Results
- `kakao_notify` now catches `HTTPError`, `URLError`, `OSError`, and any unexpected exception, logs to stderr with an `[AI Relay] kakao_notify ...` prefix, and returns `False`. Successful sends still return `True`.
- HUMAN_REQUIRED branch still posts the GitHub comment first and is unaffected by kakao failure.
- 5 new tests cover: silent skip without webhook, success on injected sender, URLError → return False + stderr log, RuntimeError → return False + stderr log, end-to-end HUMAN_REQUIRED returning True with a posted GitHub comment when kakao raises URLError.
- Pytest cumulative: 80 → 85. Final run: `85 passed in 0.38s`.

### Failed Tests
- None.

### Logs
- `85 passed in 0.38s`

### Screenshots / Runtime Evidence
- Not applicable for stdlib-only Python harness.

### Not Verified
- Live kakao webhook delivery (no webhook secret in this environment).

## 2026-05-10 Stage 6: Risks 7-10 Fixes

### Commands Run
- `python3 -m py_compile .github/scripts/ai_relay_harness.py`
- `python3 -m pytest -q`

### Results
- Risk 7 (network retry + visible error comment): `github_api_request` retries on URLError/429/5xx with injectable backoff/sleeper/opener; `main()` posts `[AI Relay Error]` on `RelayHarnessError`.
- Risk 8 (hidden-state hijack guard): `latest_hidden_payload` prefers highest comment id, skips edited comments, falls back to reverse-iteration without id fields.
- Risk 9 (DONE→start continuity): `/relay start` blocked while latest hidden state is DONE unless `force: true`; counters carry forward via `prior_state` argument.
- Risk 10 (code-block marker collision): `extract_hidden_json` requires column-0 marker outside fenced code blocks.
- Pytest cumulative growth: 69 → 80. Final run: `80 passed in 0.32s`.
- Risk 11 newly identified during this stage (kakao network failure cascading to red workflow); deferred.

### Failed Tests
- None.

### Logs
- `80 passed in 0.32s`

### Screenshots / Runtime Evidence
- Not applicable for stdlib-only Python harness.

### Not Verified
- Live GitHub API retry path (no network access from this container; tests use injected opener/sleeper).
- Live kakao webhook delivery during HUMAN_REQUIRED.
- Risk 11 (kakao network failure mid-page) — code path exists but no try/except guard yet.

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
