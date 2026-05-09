# AI Evidence

## Commands Run
- `pytest -q`
- `python -m py_compile .github/scripts/ai_relay_harness.py tests/test_ai_relay_harness.py`
- `GITHUB_EVENT_PATH="$tmpdir/event.json" GITHUB_REPOSITORY=owner/repo GITHUB_TOKEN=fake python .github/scripts/ai_relay_harness.py "$tmpdir"` with a non-status event
- Checked the workflow file for the forbidden workflow trigger.

## Results
- `pytest -q`: passed, 5 tests.
- `python -m py_compile .github/scripts/ai_relay_harness.py tests/test_ai_relay_harness.py`: passed.
- Non-status CLI event check: passed with `No /relay status command found.`
- Forbidden workflow trigger absence check: passed.

## Failed Tests
- None.

## Logs
```txt
.....                                                                    [100%]
5 passed in 0.06s
```

## Screenshots / Runtime Evidence
- Not applicable; this change only adds a GitHub Actions issue comment handler.

## Not Verified
- Live GitHub API posting was not executed locally; tests use an injected comment poster to verify issue-number routing and response content.
