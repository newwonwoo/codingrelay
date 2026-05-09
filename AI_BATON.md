# AI Baton

## Task Goal
- Ensure `.github/scripts/ai_relay_harness.py` treats every chapter 7 root relay file as required, including `AGENTS.md` and `AI_DECISIONS.md`.
- Implement V1 `/relay status` handling for GitHub issue comments and PR comment threads, posting the current relay status back as an Issue comment.

## Current Agent
- Codex

## Next Agent
- Claude

## Work Completed
- Created the AI relay harness with the complete chapter 7 `REQUIRED_FILES` list.
- Added regression tests confirming `AGENTS.md` and `AI_DECISIONS.md` omissions raise `Missing required file:` errors.
- Added root relay documentation files so the repository satisfies the harness contract.
- Added `/relay status` detection for `issue_comment` payloads.
- Added `AI_RELAY_STATE.json` loading with default READY state fallback when the state file is absent.
- Added status response formatting matching the requested V1 response shape.
- Added GitHub Issue comment posting through the issues comments API using `GITHUB_TOKEN`.
- Added a GitHub Actions `issue_comment` workflow that invokes the harness and supports PR threads through the shared issue number.
- Kept `/relay start` unimplemented; tests assert it is ignored.

## Changed Files
- `.github/scripts/ai_relay_harness.py`
- `.github/workflows/ai-relay.yml`
- `tests/test_ai_relay_harness.py`
- `AGENTS.md`
- `AI_RELAY_CONTRACT.md`
- `AI_RELAY_STATE.json`
- `AI_BATON.md`
- `AI_DECISIONS.md`
- `AI_EVIDENCE.md`
- `AI_RISKS.md`

## Decision Reasons
- Chapter 7 defines seven required repository-root files, so the harness constant now lists all seven explicitly.
- Tests use temporary repositories to verify missing-file errors without depending on the working tree state.
- The issue_comment payload's `issue.number` is used for both issues and PRs because GitHub PR conversations are also issue threads for the comments API.
- The status handler skips full required-file validation so an absent `AI_RELAY_STATE.json` can correctly fall back to the default READY status.

## Evidence
- Test: `pytest -q` passed with 7 tests.
- Build: Not applicable; Python validation harness only.
- Lint: Not run; no project linter is configured.
- Typecheck: Not run; no project typechecker is configured.
- Manual Check: `python .github/scripts/ai_relay_harness.py .` passed.

## Known Risks
- No packaging metadata exists, so tests import the harness by file path.
- Live GitHub API posting is not exercised in local tests; the network boundary is isolated behind `post_issue_comment` and covered with an injected fake poster.

## Six-Month Failure Risks
- Future chapter 7 changes could make the hard-coded required file list stale.
- GitHub API header requirements may change, requiring updates to `post_issue_comment`.

## Receiver Compatibility Risks
- A receiving agent may expect an older harness file to exist in history, but this repository previously contained only the design document.
- A receiving agent may mistake `/relay start` as partially implemented; it is intentionally ignored in V1.

## Do Not Touch
- Do not remove chapter 7 required files from `REQUIRED_FILES` without updating the design and tests.
- Do not implement `/relay start` until it is explicitly requested.

## Next Actions
- Review the committed changes and merge if the relay status comment behavior is acceptable.

## Handoff Status
PASS
