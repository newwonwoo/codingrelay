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
