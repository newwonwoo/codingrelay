# AI Risks

## Six-Month Failure Risks

### Risk 1
- Problem: The root required file list may drift if the design document changes.
- Future Symptom: Harness validation passes while newly required relay files are absent.
- Fix: Update `REQUIRED_FILES` and its tests whenever chapter 7 changes.

### Risk 2
- Problem: GitHub's issue comments API or required headers may change.
- Future Symptom: `/relay status` is detected but the action fails while posting the response comment.
- Fix: Update `post_issue_comment` and the workflow permissions according to the current GitHub Actions API guidance.

## Receiver Compatibility Risks

### Risk 1
- Problem: Agents may confuse repository-root required files with optional workflow files.
- Why Next Agent May Misunderstand: Optional files are also documented near the required file list.
- Fix: Keep tests asserting only the seven required root files.

### Risk 2
- Problem: `/relay status` and `/relay start` are adjacent commands conceptually, but V1 only implements status.
- Why Next Agent May Misunderstand: The workflow triggers on all issue comments and the harness filters commands internally.
- Fix: Preserve the test that verifies `/relay start` is ignored until start behavior is explicitly requested.
