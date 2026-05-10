# AI Baton

## Task Goal
- Land V1 of the relay orchestrator end-to-end: regression CI gate, the
  `/relay accept|reject|stop|fix` command surface, automated baton/evidence
  handoff gate, `HUMAN_REQUIRED` enforcement on limit breaches, kakao
  notification interface, and a tragic-failure-premise audit feeding into
  `AI_RISKS.md`.

## Current Agent
- claude

## Next Agent
- codex

## Work Completed
- Stage 1: `.github/workflows/ai-relay-tests.yml` runs `py_compile` + `pytest`
  on every PR and push to main, closing Risk 6. `/relay accept` swaps agents
  and increments round; `/relay reject` keeps current agent, bumps
  `receiver_reject_count`, and emits a self-fix prompt with the supplied
  `reason:` line.
- Stage 2: `check_baton_required`, `check_evidence_required`, and
  `evaluate_handoff_gate` validate required sections in `AI_BATON.md` /
  `AI_EVIDENCE.md` and the `Handoff Status` value. `/relay verify` now
  appends a `Handoff gate: PASS|BLOCK + reasons` block automatically.
- Stage 3: `evaluate_limit_breach`, `enforce_limits`,
  `format_human_required_comment`. `build_handoff_state` and
  `build_reject_state` route through `enforce_limits` so any counter past
  its `max_*` lands in `HUMAN_REQUIRED`. The event handler short-circuits
  every command except `/relay status` (and Stage 4's `/relay stop`) when
  the resolved hidden state is locked.
- Stage 4: `/relay stop` (`status=DONE`, optional `reason:`, always honored)
  and `/relay fix` (`status=NEEDS_SELF_FIX`, `self_fix_count++`, embeds the
  current gate failures as a self-fix prompt). `format_self_fix_prompt`
  follows orchestrator §20.4 and never emits `@claude`/`@codex`.
- Stage 5-A tragic-failure premise audit: produced four new entries in
  `AI_RISKS.md` (Risk 7 network errors, Risk 8 hidden-state hijacking via
  edits, Risk 9 DONE→start round history loss, Risk 10 code-block marker
  collision). Two findings fixed immediately: `build_start_state` folds
  `max_*` from `AI_RELAY_STATE.json` into the hidden state on `/relay
  start`; `CLAUDE.md` and `CODEX.md` now document the full command surface.
- Stage 5-B: `kakao_notify(message, *, webhook_url, sender)` interface with
  injectable sender for tests, wired into the `HUMAN_REQUIRED` short-circuit
  so the operator gets paged when limits trip. Workflow `.github/workflows/
  ai-relay.yml` now passes `KAKAO_WEBHOOK_URL` from secrets (silent skip
  when unset).

## Changed Files
- `.github/scripts/ai_relay_harness.py`
- `.github/workflows/ai-relay.yml`
- `.github/workflows/ai-relay-tests.yml` (new)
- `tests/test_ai_relay_harness.py`
- `tests/fixtures/issue_comment_accept.json` (new)
- `tests/fixtures/issue_comment_reject.json` (new)
- `tests/fixtures/issue_comment_stop.json` (new)
- `tests/fixtures/issue_comment_fix.json` (new)
- `CLAUDE.md`
- `CODEX.md`
- `docs/ai-relay-v1-implementation-plan.md`
- `AI_BATON.md`
- `AI_EVIDENCE.md`
- `AI_RISKS.md`
- `AI_DECISIONS.md`
- `AI_RELAY_STATE.json`

## Decision Reasons
- Each stage shipped as a single commit with both code and tests so the CI
  gate can bisect a regression to one stage.
- Public function signatures unchanged; new behavior added by either new
  functions or optional parameters with safe defaults. Existing tests stay
  green throughout.
- Kakao delivery is interface-only by default (silent without
  `KAKAO_WEBHOOK_URL`) so the harness keeps working in repos that have not
  configured the secret.
- The tragic-failure audit's larger findings (network retries,
  hidden-state hijack guard, DONE→start round preservation, code-block
  marker collision) are documented as Risks 7-10 instead of fixed inline,
  to keep this round's diff reviewable.

## Evidence
- Test: `python3 -m pytest -q` — 69 passed in 0.37s
- Build: not applicable for stdlib-only Python harness
- Lint: `python3 -m py_compile .github/scripts/ai_relay_harness.py` exit 0
- Typecheck: not applicable
- Manual Check: ran tragic-failure audit (orchestrator §13.2) over the eight
  failure categories; four findings fixed inline, four converted into
  Risks 7-10.

## Known Risks
- Kakao delivery is not exercised live in this repo; `kakao_notify` only
  prints/sends when `KAKAO_WEBHOOK_URL` is set. The injected-sender test
  proves wiring but not real delivery.
- `/relay verify` BLOCK output reflects only the current repo checkout's
  baton/evidence files. If a CI runner checks out an unrelated commit, the
  gate verdict can disagree with the live PR thread state.
- DONE → `/relay start` resets all counters; this is documented in Risk 9
  but not yet fixed.

## Six-Month Failure Risks
- See `AI_RISKS.md` Risks 7-10 for the audit findings deferred from this
  round. The Stage 1 CI gate is the primary defense against another
  PR-#16-style regression.

## Receiver Compatibility Risks
- The next agent may want to address Risks 7-10 immediately. Each is
  additive and can be done as a separate small PR. Do not collapse them
  into one large rewrite.
- Public function signatures are stable as of this round. New work should
  add optional parameters or new functions rather than reshape existing
  ones; the test suite asserts current shapes.

## Do Not Touch
- Do not introduce live `@claude`/`@codex` mentions, skill loading, auto
  merge, dashboards, or multi-repo orchestration. V1 boundary is unchanged.
- Do not remove the `KAKAO_WEBHOOK_URL` silent-skip path; live delivery is
  opt-in by design.
- Do not change the hidden marker format (`<!-- AI_RELAY_STATE` /
  `<!-- AI_RELAY_PLAN`) without a migration path; old comments must remain
  parseable.

## Stage 7 Addendum (Risk 11 landed)

- `kakao_notify` now wraps both the injectable `sender` path and the
  real `urlopen` path in try/except. `HTTPError`, `URLError`, `OSError`,
  and any unexpected exception are caught, logged to stderr with the
  `[AI Relay] kakao_notify ...` prefix, and the function returns `False`.
- HUMAN_REQUIRED branch unchanged at the call site — it already ignored
  the return value, so isolating the failure required no caller changes.
- Test count: 85 passing (80 + 5 new for Risk 11).
- All four originally-deferred risks (7-10) and the newly discovered
  Risk 11 are now closed. AI_RISKS.md has zero open items.

## Stage 6 Addendum (Risks 7-10 landed)

- `github_api_request` retries on URLError, HTTP 429, and HTTP 5xx with
  2s/4s/8s backoff. On exhaustion or non-retryable HTTP errors raises
  `RelayHarnessError`; `main()` catches it and best-effort posts an
  `[AI Relay Error]` comment so the user sees a visible failure.
- `latest_hidden_payload` prefers the GitHub comment with the highest
  numeric `id` (creation order) and skips comments where
  `created_at != updated_at`. Test fixtures without `id` keep working
  via reverse-iteration fallback.
- `/relay start` refuses to run when the latest hidden state is `DONE`
  unless the comment includes `force: true`. With `force: true`,
  `build_start_state` carries forward `round`, `self_fix_count`,
  `receiver_reject_count`, and `max_*` from the prior state.
- `extract_hidden_json` requires the marker to start at column 0 and
  not be inside a fenced code block.
- New Risk 11 documented (kakao webhook unreachable cascading to red
  workflow). Code path exists but no try/except guard yet.
- Test count: 80 passing. py_compile clean.

## Next Actions
- Risk 11 (kakao notify failure isolation) — wrap the call in
  HUMAN_REQUIRED branch with try/except.
- Optional: live kakao webhook smoke test once a webhook secret is
  provisioned in repo settings.
- Optional: live GitHub Actions retry-path verification once the PR is
  exercised on a flaky-API window.

## Handoff Status
PASS
