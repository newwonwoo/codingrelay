# AI Decisions

## 2026-05-09

- Added the full chapter 7 root required file set to the relay harness `REQUIRED_FILES` list.
- Added focused pytest coverage for missing `AGENTS.md` and `AI_DECISIONS.md` validation errors.
- Implemented V1 `/relay status` issue-comment handling in the harness without adding `/relay start` behavior.
- Added a GitHub Actions issue_comment workflow that uses `GITHUB_TOKEN` to post status responses back to the issue or PR thread by issue number.
