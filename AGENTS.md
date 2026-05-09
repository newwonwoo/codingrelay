# Repository Agent Instructions

This repository uses the AI Relay workflow described in `AI_RELAY_CONTRACT.md`.

## Required Agent Behavior

1. Read `AI_RELAY_CONTRACT.md` before changing code.
2. Keep changes as small and reversible as possible.
3. Update relay evidence files when work is performed:
   - `AI_BATON.md`
   - `AI_EVIDENCE.md`
   - `AI_RISKS.md`
   - `AI_DECISIONS.md` when a meaningful decision is made
4. Do not hand off without evidence.
5. Do not include secrets, tokens, credentials, or `.env` values in relay files or comments.

## MVP Boundary

For V1 skeleton work, prefer thin GitHub Actions harness behavior over model-calling automation. Do not add dashboards, merge automation, multi-repository orchestration, or complex permission systems unless explicitly requested.
