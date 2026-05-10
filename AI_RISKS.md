# AI Risks

## Six-Month Failure Risks

### Risk 1
- Problem: GitHub event payload handling is currently skeletal.
- Future Symptom: `/relay` commands may be ignored or misclassified when Phase 2 begins.
- Fix: Add command-parser fixtures for issue comments, PR events, workflow runs, and manual dispatch.

### Risk 2
- Problem: Kakao notification is not wired to a provider yet.
- Future Symptom: HUMAN_REQUIRED status may not alert a human outside GitHub.
- Fix: Add a provider interface and secret-backed sender in the Kakao notification phase.

## Receiver Compatibility Risks

### Risk 1
- Problem: Phase 1 creates only the structure and validation harness, not the full orchestrator.
- Why Next Agent May Misunderstand: The presence of workflow files may look like complete automation.
- Fix: Keep MVP boundaries explicit in `docs/ai-relay-v1-implementation-plan.md` and relay evidence files.


### Risk 3
- Problem: Local validation can pass while live GitHub Actions dispatch remains unverified when the container has no `gh` CLI, no authenticated GitHub API context, and no configured remote.
- Future Symptom: The harness may appear ready locally, but the repository owner may still not see a Run workflow button or may see a GitHub-only workflow validation error.
- Fix: Push the branch to GitHub, run the PR check or `workflow_dispatch` from the GitHub UI/API, and record the live run result in `AI_EVIDENCE.md`.

### Risk 4
- Problem: `/relay dispatch` relies on the latest hidden state comment and line-oriented `/relay plan` fields.
- Future Symptom: Dispatch may use stale or incomplete plan text if comments are reordered, truncated, or users provide multi-line plan values.
- Fix: Add explicit plan IDs or structured blocks if the command format grows beyond MVP single-line fields.

### Risk 5
- Problem: `/relay dispatch` renders a prompt from hidden state and hidden plan but does not validate plan completeness beyond defaults.
- Future Symptom: A dispatch comment may be syntactically valid but too vague if goal, scope, or done are empty.
- Fix: Add explicit BLOCK/HUMAN_REQUIRED validation once prompt rendering is stable.

### Risk 6
- Problem: PR #16 merged into `main` with both `.github/scripts/ai_relay_harness.py` and `tests/test_ai_relay_harness.py` left in a SyntaxError state — duplicated function definitions and stray `return` statements from a manual conflict resolution. No CI gate catches this because the workflow does not run `py_compile` or `pytest` on PRs.
- Future Symptom: Any future hand-resolved merge between two relay feature branches can land on `main` with the harness un-importable; `/relay` commands silently fail in the workflow with no obvious signal until a user looks at the Action logs.
- Fix: Resolved in Stage 1 — `.github/workflows/ai-relay-tests.yml` runs `py_compile` and `pytest -q` on every PR + push to main.

### Risk 7
- Problem: `github_api_request` (`urlopen`) does not catch `HTTPError`/`URLError`/timeout. A transient GitHub API failure during `list_issue_comments` or `post_issue_comment` will surface as an uncaught exception, which the workflow turns into a job failure but no useful comment.
- Future Symptom: Six months in, a flaky GitHub API window will cause `/relay` commands to appear silently broken — no comment posted, only a red CI check.
- Fix: Wrap `github_api_request` callers in retry-with-backoff (3 tries, 2s/4s/8s) and post a short `[AI Relay Error]` comment when retries are exhausted, so the user sees what happened.

### Risk 8
- Problem: `latest_hidden_state` / `latest_hidden_plan` walk the comment list in reverse and return the newest hidden marker. A user (or a malicious actor with comment-edit rights) can edit an old comment to insert a hidden marker block, hijacking the "latest" detection.
- Future Symptom: Relay state silently rolls back to a stale or attacker-controlled value without any visible indication.
- Fix: Track each hidden marker's GitHub `comment.id` and prefer the highest `id` over reverse-iteration; reject markers found in edited comments where `created_at != updated_at` unless explicitly allowed.

### Risk 9
- Problem: After `/relay stop` sets `status=DONE`, a subsequent `/relay start` builds a fresh hidden state with `round=0` and no link to the prior session. Round/self_fix/receiver_reject history is lost.
- Future Symptom: A second pass on the same task starts with full limits available, defeating the stop-control invariant for tasks that should be considered exhausted.
- Fix: Carry over `task_id` and the previous `round` totals into the new hidden state, or refuse `/relay start` while the latest hidden state is `DONE` unless the user includes `force: true`.

### Risk 10
- Problem: `extract_hidden_json` matches the literal string `<!-- AI_RELAY_STATE` anywhere in the body. A user pasting an example hidden marker inside a fenced code block in a comment will be parsed as real state.
- Future Symptom: Documentation, debugging tutorials, or test fixtures pasted into a real PR comment can poison the hidden state and corrupt routing.
- Fix: Require the marker to be at the top of the comment (or at column 0) and add a regression test for code-block-fenced markers being ignored.
