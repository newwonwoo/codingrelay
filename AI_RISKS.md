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
- Problem: `github_api_request` (`urlopen`) did not catch `HTTPError`/`URLError`/timeout. A transient GitHub API failure during `list_issue_comments` or `post_issue_comment` surfaced as an uncaught exception, which the workflow turned into a job failure with no useful comment.
- Future Symptom: A flaky GitHub API window would have caused `/relay` commands to appear silently broken — no comment posted, only a red CI check.
- Fix (Stage 6 — landed): `github_api_request` now retries on `URLError`, HTTP 429, and HTTP 5xx with a 2s/4s/8s backoff (overridable via `backoff=`/`sleeper=`/`opener=` for tests). On exhaustion or non-retryable errors it raises `RelayHarnessError`. `main()` catches that and best-effort posts a single `[AI Relay Error]` comment with the reason, so users see a visible failure.

### Risk 8
- Problem: `latest_hidden_state` / `latest_hidden_plan` walked the comment list in reverse and returned the first hidden marker found. A user (or a malicious actor with comment-edit rights) could edit an old comment to insert a hidden marker block, hijacking the "latest" detection.
- Future Symptom: Relay state would silently roll back to a stale or attacker-controlled value with no visible indication.
- Fix (Stage 6 — landed): `latest_hidden_payload` now prefers the GitHub comment with the highest numeric `id` (creation order) over reverse-iteration, and skips comments whose `updated_at != created_at`. Test fixtures without `id` fields fall back to reverse-iteration to preserve existing behavior.

### Risk 9
- Problem: After `/relay stop` set `status=DONE`, a subsequent `/relay start` built a fresh hidden state with `round=0` and no link to the prior session. Round / self_fix_count / receiver_reject_count history was lost.
- Future Symptom: A second pass on the same task started with full limits available, defeating the stop-control invariant for tasks that should be considered exhausted.
- Fix (Stage 6 — landed): When the latest hidden state is `DONE`, `/relay start` is refused unless the comment includes `force: true`; the response is `[AI Relay Start Blocked]`. With `force: true`, `build_start_state` carries forward `round`, `self_fix_count`, `receiver_reject_count`, and `max_*` from the prior state into the new hidden state.

### Risk 10
- Problem: `extract_hidden_json` matched the literal string `<!-- AI_RELAY_STATE` anywhere in the body. A user pasting an example hidden marker inside a fenced code block was parsed as real state.
- Future Symptom: Documentation, debugging tutorials, or test fixtures pasted into a real PR comment could poison the hidden state and corrupt routing.
- Fix (Stage 6 — landed): `extract_hidden_json` requires the marker line to start at column 0 and not be inside a ```` ``` ```` or `~~~` fenced code block. Regression tests assert that fenced and indented markers are ignored while canonical markers still parse.

### Risk 11
- Problem: When the kakao webhook was configured but unreachable, `kakao_notify` raised on `urlopen` and bubbled up to `main()`. Since the HUMAN_REQUIRED short-circuit calls `kakao_notify` *after* posting the GitHub comment, the relay state was preserved, but the workflow run still ended red.
- Future Symptom: A team monitoring red workflow runs would have gotten a false positive every time the kakao host had a hiccup, even though the relay state was successfully persisted on GitHub.
- Fix (Stage 7 — landed): `kakao_notify` now wraps both the injectable `sender` path and the real `urlopen` path in a try/except that catches `HTTPError`, `URLError`, `OSError`, and any unexpected exception. Failures are logged to stderr with an `[AI Relay] kakao_notify ...` prefix and the function returns `False`. Callers (HUMAN_REQUIRED branch in `handle_issue_comment_event`) are unaffected because they already ignored the return value. Regression tests assert: silent skip without webhook, success on injected sender, return-False + stderr log on URLError, return-False + stderr log on RuntimeError, and end-to-end HUMAN_REQUIRED path still returns True with a posted comment when the real `urlopen` raises URLError.
