# Skill-Based Bidirectional AI Relay Orchestrator V1

## 0. 문서 목적

이 문서는 Claude Code와 Codex를 양방향으로 교대 투입하는 AI 개발 오케스트레이터의 V1 설계서다.

핵심은 단순히 두 모델을 번갈아 호출하는 것이 아니다.

현재 작업 Agent가 자기검증을 수행하고, 6개월 후 고장 가능성을 검토하며, 증거를 남기고, 다음 Agent가 수신검증을 통과한 뒤에만 작업을 이어받게 만드는 것이다.

---

## 1. 한 줄 정의

모델 중립 Baton Protocol을 기반으로 Claude Code와 Codex를 양방향 교대 투입하고, 각 인수인계 전 자기검증, 6개월 후 실패검증, 증거검증, 수신검증을 강제하는 AI 개발 오케스트레이터.

---

## 2. 핵심 개념

### 2.1 Agent

Agent는 특정 모델명이 아니라 역할이다.

- Current Agent: 현재 코드를 수정하는 모델
- Next Agent: 다음에 이어받을 모델
- Receiving Agent: Baton을 받고 수락 여부를 판단하는 모델
- Orchestrator: 상태를 읽고 다음 행동을 결정하는 제어기

예시:

```txt
Claude가 작업 중이면:
Current Agent = Claude
Next Agent = Codex

Codex가 작업 중이면:
Current Agent = Codex
Next Agent = Claude
```

---

## 3. 기본 철학

```txt
1. 모델 이름이 아니라 역할 중심으로 설계한다.
2. Claude/Codex는 Agent A/B로 추상화한다.
3. 코딩한 모델이 1차 자기검증 책임을 진다.
4. 받는 모델은 수락검증 후에만 작업한다.
5. 증거 없는 인수인계는 금지한다.
6. 무한 핑퐁을 방지한다.
7. 사람은 목표와 최종판단에 집중한다.
```

핵심 원칙:

```txt
No handoff without evidence.
```

---

## 4. 전체 플로우

```txt
사용자 목표 입력
↓
시작 Agent 선택
  - Claude
  - Codex
  - Auto
↓
Current Agent 작업
↓
Current Agent 자기검증
↓
6개월 후 실패 가능성 검토
↓
오케스트레이터 증거검증
↓
Next Agent 수신검증
↓
수락 시 Next Agent 작업
↓
반복 또는 완료
```

---

## 5. V1에서 구현할 것

```txt
1. GitHub Issue/PR 댓글 명령 파싱
2. AI_RELAY_STATE.json 읽기/쓰기
3. AI_BATON.md 필수 항목 검사
4. GitHub Actions 테스트 결과 읽기
5. @claude / @codex 댓글 자동 작성
6. Self Verification Prompt 자동 작성
7. Receiver Acceptance Prompt 자동 작성
8. max_rounds 초과 시 HUMAN_REQUIRED 전환
9. 카톡 알림 연동
```

---

## 6. V1에서 하지 말 것

```txt
1. 예쁜 대시보드
2. 완전 자동 merge
3. 토큰 잔량 직접 감지
4. 보안 감사 전체 자동화
5. 여러 레포 동시 제어
6. 복잡한 권한 시스템
7. 자체 코드 에디터
8. 모델 성능 점수화
```

---

## 7. 레포 파일 구조

레포 루트에 아래 파일을 둔다.

```txt
/AGENTS.md
/AI_RELAY_CONTRACT.md
/AI_RELAY_STATE.json
/AI_BATON.md
/AI_DECISIONS.md
/AI_EVIDENCE.md
/AI_RISKS.md
```

선택 파일:

```txt
/CLAUDE.md
/CODEX.md
/.github/workflows/ai-relay.yml
```

---

## 8. 핵심 파일 상세

### 8.1 AI_RELAY_CONTRACT.md

모든 Agent가 따르는 중립 계약서다.

```md
# AI Relay Contract

## Core Rule

This repository uses a bidirectional AI relay workflow.

## Agent Roles

- Current Agent: the model currently modifying code.
- Next Agent: the model expected to continue work.
- Receiving Agent: the model that checks whether it can accept the Baton.
- Orchestrator: the controller that validates state and decides next action.

## Mandatory Flow

1. Understand the task.
2. Make the smallest safe change.
3. Record changed files.
4. Provide evidence.
5. Run self-verification.
6. Identify six-month failure risks.
7. Prepare Baton.
8. Do not hand off if BLOCK conditions remain.

## Forbidden

- Do not hide failed tests.
- Do not claim completion without evidence.
- Do not rewrite large areas unless explicitly requested.
- Do not remove previous Agent decisions without explaining why.
- Do not include secrets or credentials in Baton.

## Handoff Rule

No handoff without evidence.
```

---

### 8.2 AI_BATON.md

Agent 간 인수인계 문서다.

```md
# AI Baton

## Task Goal
-

## Current Agent
-

## Next Agent
-

## Work Completed
-

## Changed Files
-

## Decision Reasons
-

## Evidence
- Test:
- Build:
- Lint:
- Typecheck:
- Manual Check:

## Known Risks
-

## Six-Month Failure Risks
-

## Receiver Compatibility Risks
-

## Do Not Touch
-

## Next Actions
-

## Handoff Status
PASS / CONDITIONAL_PASS / BLOCK
```

---

### 8.3 AI_RELAY_STATE.json

오케스트레이터가 읽는 상태파일이다.

```json
{
  "task_id": "",
  "issue_number": null,
  "pr_number": null,
  "current_agent": "claude",
  "next_agent": "codex",
  "status": "READY",
  "round": 0,
  "self_fix_count": 0,
  "receiver_reject_count": 0,
  "max_rounds": 3,
  "max_self_fix": 2,
  "max_receiver_reject": 1,
  "last_test_status": "unknown",
  "handoff_status": "unknown",
  "requires_human": false
}
```

---

### 8.4 AI_EVIDENCE.md

테스트, 빌드, 로그, 수동검증 결과를 기록한다.

```md
# AI Evidence

## Commands Run
-

## Results
-

## Failed Tests
-

## Logs
-

## Screenshots / Runtime Evidence
-

## Not Verified
-
```

---

### 8.5 AI_RISKS.md

장기 고장 가능성과 인수인계 취약점을 기록한다.

```md
# AI Risks

## Six-Month Failure Risks

### Risk 1
- Problem:
- Future Symptom:
- Fix:

## Receiver Compatibility Risks

### Risk 1
- Problem:
- Why Next Agent May Misunderstand:
- Fix:
```

---

## 9. 상태값

```txt
READY
WORKING
SELF_VERIFYING
NEEDS_SELF_FIX
EVIDENCE_CHECKING
READY_FOR_HANDOFF
RECEIVER_REVIEWING
ACCEPTED_BY_RECEIVER
REJECTED_BY_RECEIVER
WORKING_BY_NEXT_AGENT
BLOCKED
DONE
HUMAN_REQUIRED
```

---

## 10. 상태 전이 규칙

### 10.1 시작

```txt
READY
↓
WORKING
```

조건:

```txt
/relay start 명령 수신
```

---

### 10.2 작업 완료 후 자기검증

```txt
WORKING
↓
SELF_VERIFYING
```

조건:

```txt
Current Agent가 작업 완료 또는 PR 업데이트
```

---

### 10.3 자기검증 실패

```txt
SELF_VERIFYING
↓
NEEDS_SELF_FIX
```

조건:

```txt
AI_BATON.md 필수 항목 누락
테스트 결과 누락
Handoff Status = BLOCK
```

---

### 10.4 자기검증 통과

```txt
SELF_VERIFYING
↓
RECEIVER_REVIEWING
```

조건:

```txt
Handoff Status = PASS 또는 CONDITIONAL_PASS
Evidence 존재
```

---

### 10.5 수신 거절

```txt
RECEIVER_REVIEWING
↓
REJECTED_BY_RECEIVER
↓
NEEDS_SELF_FIX
```

조건:

```txt
Receiving Agent가 REJECT 판단
```

---

### 10.6 수신 수락

```txt
RECEIVER_REVIEWING
↓
ACCEPTED_BY_RECEIVER
↓
WORKING
```

조건:

```txt
Receiving Agent가 ACCEPT 또는 ACCEPT_WITH_WARNINGS 판단
```

이때 current_agent와 next_agent를 swap한다.

---

### 10.7 반복 제한 초과

```txt
ANY
↓
HUMAN_REQUIRED
```

조건:

```txt
round > max_rounds
self_fix_count > max_self_fix
receiver_reject_count > max_receiver_reject
```

---

## 11. Agent 선택 기준

### 11.1 사용자가 직접 선택

사용자 선택을 우선한다.

```txt
start_agent: claude
start_agent: codex
```

---

### 11.2 자동 선택 기준

| 작업 유형 | 추천 시작 Agent |
|---|---|
| 구조 파악 | Claude |
| 설계 변경 | Claude |
| 리팩터링 판단 | Claude |
| 원인 불명 | Claude |
| 테스트 실패 수정 | Codex |
| 작은 버그 수정 | Codex |
| CI 실패 해결 | Codex |
| 구현 디테일 많은 작업 | Codex |

---

## 12. Skill 기반 설계

이 오케스트레이터는 모델을 직접 호출하는 봇이 아니라, 상태에 따라 필요한 Skill을 선택하고 그 Skill을 Agent에게 실행시키는 구조다.

### 12.1 V1 Skill 목록

```txt
1. intake-skill
2. agent-selection-skill
3. build-skill
4. self-verification-skill
5. six-month-failure-skill
6. receiver-compatibility-skill
7. receiver-acceptance-skill
8. evidence-gate-skill
9. baton-packaging-skill
10. stop-control-skill
```

---

### 12.2 intake-skill

사용자 목표를 작업 단위로 정리한다.

입력:

```txt
- 사용자 목표
- 관련 Issue/PR
- 시작 Agent 선택
```

출력:

```txt
- 작업 목표
- 범위
- 제외 범위
- 완료 기준
```

---

### 12.3 agent-selection-skill

시작 Agent와 다음 Agent를 결정한다.

입력:

```txt
- 작업 유형
- 실패 로그 여부
- 사용자 선택
```

출력:

```txt
- current_agent
- next_agent
- reason
```

---

### 12.4 build-skill

실제 코드 수정 지시다.

원칙:

```txt
- 최소 변경
- 기존 구조 존중
- 테스트 우선
- 변경 이유 기록
```

---

### 12.5 self-verification-skill

작업한 Agent가 자기검증한다.

핵심:

```txt
- 자기 합리화 금지
- 실패 숨김 금지
- 증거 없는 완료 금지
```

---

### 12.6 six-month-failure-skill

6개월 후 장애를 가정한다.

질문:

```txt
이 변경이 6개월 후 망가진다면 어디서 망가지는가?
```

검사 항목:

```txt
1. 하드코딩
2. 테스트 부재
3. 외부 의존성 취약
4. 상태 전이 불명확
5. 숨은 결합도
6. 로그 부족
7. 예외처리 부족
8. 문서 불일치
```

---

### 12.7 receiver-compatibility-skill

상대 모델이 이어받을 때 생길 문제를 찾는다.

질문:

```txt
다음 Agent가 이 작업을 오해하거나 되돌릴 위험은 무엇인가?
```

---

### 12.8 receiver-acceptance-skill

받는 모델이 수락 여부를 판단한다.

결과:

```txt
ACCEPT
ACCEPT_WITH_WARNINGS
REJECT
```

---

### 12.9 evidence-gate-skill

테스트, 빌드, 로그, 수동검증을 확인한다.

판단 기준:

```txt
No handoff without evidence.
```

---

### 12.10 baton-packaging-skill

다음 Agent가 바로 이어받을 수 있게 정보를 포장한다.

필수 정보:

```txt
1. 목표
2. 변경파일
3. 결정이유
4. 검증증거
5. 리스크
6. 금지구역
7. 다음액션
```

---

### 12.11 stop-control-skill

릴레이 중단 조건을 판단한다.

중단 조건:

```txt
- 반복 횟수 초과
- 동일 실패 반복
- 수신 거절 반복
- 테스트 불가
- 사람 판단 필요
```

---

## 13. 검증 게이트

### 13.1 Self Verification Gate

작업한 Agent가 스스로 답해야 한다.

```md
## Self Verification

1. 내가 바꾼 파일은 무엇인가?
2. 왜 바꿨는가?
3. 요구사항을 정확히 만족했는가?
4. 테스트 또는 검증 증거는 무엇인가?
5. 실패하거나 확인하지 못한 것은 무엇인가?
6. 내가 과하게 바꾼 부분은 없는가?
7. 다음 Agent가 오해할 가능성은 무엇인가?
```

---

### 13.2 Six-Month Failure Gate

작업이 6개월 후 망가졌다고 가정한다.

```md
## Six-Month Failure Review

Assume this change breaks six months later.

Find:
1. Hardcoded assumptions
2. Missing tests
3. Fragile external dependencies
4. Unclear state transitions
5. Hidden coupling
6. Poor logging
7. Incomplete error handling
8. Documentation mismatch

For each risk:
- Problem
- Future symptom
- Prevention
```

---

### 13.3 Receiver Compatibility Gate

다음 Agent가 이어받을 때 깨질 부분을 점검한다.

```md
## Receiver Compatibility Review

Before handing off to the next Agent, check:

1. Is the goal clear?
2. Are changed files listed?
3. Are decision reasons recorded?
4. Are failed tests visible?
5. Are commands to verify included?
6. Are "do not touch" areas clear?
7. Are known risks explicit?
8. Can the next Agent continue without guessing?
```

---

### 13.4 Receiver Acceptance Gate

받는 Agent가 먼저 수락 여부를 판단한다.

```md
## Receiver Acceptance

I am the Receiving Agent.

I must decide:
- ACCEPT: I can continue safely.
- ACCEPT_WITH_WARNINGS: I can continue, but risks remain.
- REJECT: Baton is insufficient.

If REJECT:
- List missing information.
- Do not modify code yet.
```

---

## 14. PASS / BLOCK 기준

| 결과 | 의미 | 다음 액션 |
|---|---|---|
| PASS | 안전하게 넘김 | 다음 Agent 호출 |
| CONDITIONAL_PASS | 위험은 있으나 진행 가능 | 경고 포함 후 넘김 |
| BLOCK | 넘기면 안 됨 | Current Agent에게 자기수정 요청 |
| REJECTED | 받는 Agent가 거절 | Current Agent에게 Baton 보완 요청 |
| HUMAN_REQUIRED | AI끼리 해결 곤란 | 카톡 보고 |

---

## 15. 무한 핑퐁 방지

기본값:

```json
{
  "max_rounds": 3,
  "max_self_fix": 2,
  "max_receiver_reject": 1
}
```

초과 시:

```txt
상태: HUMAN_REQUIRED
카톡 보고:
AI 릴레이가 제한 횟수를 초과했습니다.
사람 판단이 필요합니다.
```

---

## 16. Relay Harness 설계

### 16.1 하네스 정의

여기서 하네스는 복잡한 프레임워크가 아니다.

GitHub 이벤트를 받아 상태를 보고, 다음 댓글/명령을 생성하는 얇은 제어기다.

---

### 16.2 V1 하네스 구성

```txt
Relay Harness
├── event_reader
├── state_loader
├── skill_selector
├── prompt_renderer
├── evidence_checker
├── baton_checker
├── transition_engine
├── github_commenter
└── kakao_notifier
```

---

### 16.3 모듈 역할

| 모듈 | 역할 |
|---|---|
| event_reader | GitHub Issue/PR/Action 이벤트 읽기 |
| state_loader | AI_RELAY_STATE.json 읽기 |
| skill_selector | 지금 실행할 skill 선택 |
| prompt_renderer | Claude/Codex용 댓글 생성 |
| evidence_checker | 테스트/빌드 결과 확인 |
| baton_checker | Baton 필수 항목 확인 |
| transition_engine | 다음 상태 결정 |
| github_commenter | @claude, @codex 댓글 작성 |
| kakao_notifier | 카톡 보고 |

---

## 17. 하네스 의사코드

```python
def run_relay(event):
    state = load_state()
    baton = load_baton()
    evidence = load_evidence()

    if state.status == "READY":
        agent = select_start_agent(event)
        post_work_prompt(agent)
        state.status = "WORKING"
        save_state(state)
        return

    if state.status == "WORKING":
        if agent_finished(event):
            post_self_verification_prompt(state.current_agent)
            state.status = "SELF_VERIFYING"
            save_state(state)
            return

    if state.status == "SELF_VERIFYING":
        result = check_self_verification(baton, evidence)

        if result == "BLOCK":
            post_self_fix_prompt(state.current_agent)
            state.status = "NEEDS_SELF_FIX"
            state.self_fix_count += 1
            save_state(state)
            return

        if result in ["PASS", "CONDITIONAL_PASS"]:
            post_receiver_acceptance_prompt(state.next_agent)
            state.status = "RECEIVER_REVIEWING"
            save_state(state)
            return

    if state.status == "RECEIVER_REVIEWING":
        acceptance = read_receiver_acceptance()

        if acceptance == "REJECT":
            state.receiver_reject_count += 1

            if state.receiver_reject_count > state.max_receiver_reject:
                state.status = "HUMAN_REQUIRED"
                notify_human()
            else:
                post_baton_fix_prompt(state.current_agent)
                state.status = "NEEDS_SELF_FIX"

            save_state(state)
            return

        if acceptance in ["ACCEPT", "ACCEPT_WITH_WARNINGS"]:
            swap_agents(state)
            post_work_prompt(state.current_agent)
            state.status = "WORKING"
            state.round += 1
            save_state(state)
            return

    if state.round > state.max_rounds:
        state.status = "HUMAN_REQUIRED"
        notify_human()
        save_state(state)
```

---

## 18. GitHub Actions 트리거

```yaml
on:
  issue_comment:
    types: [created]
  pull_request:
    types: [opened, synchronize, reopened]
  workflow_run:
    types: [completed]
  workflow_dispatch:
```

역할:

```txt
issue_comment:
- 사용자가 /relay start 입력
- Agent 작업 완료 댓글 감지
- 수신검증 결과 감지

pull_request:
- PR 생성 시 상태 초기화
- 변경 파일 확인

workflow_run:
- 테스트 결과 확인
- Evidence 업데이트

workflow_dispatch:
- 수동 재실행
```

---

## 19. 사용자 명령어

### 19.1 시작

```md
/relay start
start_agent: claude
next_agent: codex
goal: 로그인 실패 시 에러 메시지가 표시되지 않는 문제 수정
```

또는:

```md
/relay start
start_agent: codex
next_agent: claude
goal: CI에서 실패하는 auth 테스트 수정
```

---

### 19.2 상태 확인

```md
/relay status
```

---

### 19.3 강제 전환

```md
/relay handoff codex
```

```md
/relay handoff claude
```

---

### 19.4 중단

```md
/relay stop
reason: 작업 범위가 커져서 사람 검토 필요
```

---

## 20. Agent 호출 프롬프트

### 20.1 작업 프롬프트

```md
@{{current_agent}}

You are the Current Agent in a bidirectional AI relay workflow.

Read:
- AI_RELAY_CONTRACT.md
- AI_BATON.md
- AI_EVIDENCE.md
- AI_RISKS.md

Goal:
{{goal}}

Rules:
1. Make the smallest safe change.
2. Do not rewrite unrelated code.
3. Record changed files.
4. Provide evidence.
5. Update AI_BATON.md.
6. Update AI_EVIDENCE.md.
7. Update AI_RISKS.md.
8. Do not hand off yet. Prepare for self-verification.
```

---

### 20.2 자기검증 프롬프트

```md
@{{current_agent}}

Run Self Verification before handoff.

You must update AI_BATON.md and AI_RISKS.md.

Check:
1. What did you change?
2. Why did you change it?
3. What evidence proves it works?
4. What was not verified?
5. What can break six months later?
6. What can the next Agent misunderstand?
7. Is the handoff PASS, CONDITIONAL_PASS, or BLOCK?

If BLOCK, fix the issue yourself before handoff.
```

---

### 20.3 수신검증 프롬프트

```md
@{{next_agent}}

You are the Receiving Agent.

Do not modify code yet.

Read:
- AI_RELAY_CONTRACT.md
- AI_BATON.md
- AI_EVIDENCE.md
- AI_RISKS.md

Decide:
- ACCEPT
- ACCEPT_WITH_WARNINGS
- REJECT

Check:
1. Is the goal clear?
2. Are changed files and reasons clear?
3. Is evidence sufficient?
4. Are risks explicit?
5. Can you continue without guessing?

If REJECT, list exactly what is missing.
```

---

### 20.4 자기수정 프롬프트

```md
@{{current_agent}}

Your Baton or evidence failed the pre-handoff gate.

Do not hand off yet.

Fix the following before proceeding:
{{block_reasons}}

Required:
1. Update code if needed.
2. Update AI_BATON.md.
3. Update AI_EVIDENCE.md.
4. Update AI_RISKS.md.
5. Set Handoff Status to PASS, CONDITIONAL_PASS, or BLOCK.
```

---

## 21. 카톡 보고 포맷

### 21.1 시작

```txt
[AI Relay 시작]
작업: {{goal}}
현재 Agent: {{current_agent}}
다음 Agent: {{next_agent}}
상태: WORKING
```

---

### 21.2 검증 통과

```txt
[AI Relay 검증 통과]
Agent: {{current_agent}}
결과: PASS
테스트: {{test_status}}
다음: {{next_agent}} 수신검증
```

---

### 21.3 차단

```txt
[AI Relay 차단]
Agent: {{current_agent}}
상태: BLOCK
이유: {{reason}}
다음: 자기수정 요청
```

---

### 21.4 사람 필요

```txt
[AI Relay 사람 판단 필요]
작업: {{goal}}
이유: {{reason}}
권장: PR 확인 후 방향 지정
```

---

## 22. 보안 최소 규칙

V1에서 보안 감사는 제외한다.

다만 사고 방지를 위해 아래 규칙은 필수다.

```txt
1. API Key, Token, Secret은 Baton에 기록 금지
2. .env 내용 출력 금지
3. 인증정보가 로그에 나오면 마스킹
4. PR 댓글에 비밀값 복붙 금지
```

---

## 23. 개발자 구현 순서

### Phase 1. Skeleton

```txt
1. AI_RELAY_STATE.json 생성
2. AI_BATON.md 생성
3. AI_EVIDENCE.md 생성
4. AI_RISKS.md 생성
5. GitHub Action workflow 생성
```

---

### Phase 2. Command Parser

```txt
1. /relay start 파싱
2. /relay status 파싱
3. /relay stop 파싱
4. /relay handoff 파싱
```

---

### Phase 3. Prompt Renderer

```txt
1. 작업 프롬프트 생성
2. 자기검증 프롬프트 생성
3. 수신검증 프롬프트 생성
4. 자기수정 프롬프트 생성
```

---

### Phase 4. State Machine

```txt
1. READY → WORKING
2. WORKING → SELF_VERIFYING
3. SELF_VERIFYING → RECEIVER_REVIEWING
4. RECEIVER_REVIEWING → WORKING
5. 제한 초과 → HUMAN_REQUIRED
```

---

### Phase 5. Evidence Checker

```txt
1. AI_EVIDENCE.md 존재 확인
2. Commands Run 존재 확인
3. Results 존재 확인
4. Not Verified 존재 확인
5. 실패 테스트 숨김 방지
```

---

### Phase 6. Kakao Notification

```txt
1. 시작 알림
2. 검증 통과 알림
3. BLOCK 알림
4. HUMAN_REQUIRED 알림
5. DONE 알림
```

---

## 24. V1 완료 기준

```txt
1. GitHub Issue 댓글에서 /relay start 실행 가능
2. start_agent를 claude 또는 codex로 선택 가능
3. 오케스트레이터가 첫 Agent 호출 댓글 작성
4. Agent 작업 후 자기검증 댓글 작성 가능
5. Baton 필수 항목 누락 시 BLOCK 처리
6. 수신 Agent에게 acceptance prompt 작성 가능
7. ACCEPT 시 current_agent와 next_agent swap 가능
8. 반복 제한 초과 시 HUMAN_REQUIRED 처리
9. 카톡 알림 발송 가능
```

---

## 25. 개발자에게 주는 핵심 요구사항

```txt
이 툴은 Claude와 Codex를 단순 교대 호출하지 않는다.

작업 상태에 따라 필요한 Skill을 선택하고,
현재 Agent에게 작업을 배정하고,
넘기기 전 자기검증과 6개월 후 실패 가능성 검토를 수행하며,
다음 Agent가 수락 가능한 Baton 형태로 컨텍스트를 포장한다.

핵심은 모델 호출이 아니라
Skill Selection + Evidence Gate + Baton Protocol 이다.
```

---

## 26. 최종 아키텍처

```txt
User
 │
 │ /relay start
 ▼
GitHub Issue / PR
 │
 ▼
Relay Harness - GitHub Action
 │
 ├─ State Loader
 ├─ Skill Selector
 ├─ Prompt Renderer
 ├─ Evidence Checker
 ├─ Baton Checker
 ├─ Transition Engine
 ├─ GitHub Commenter
 └─ Kakao Notifier
 │
 ├──────────────▶ @claude
 │                  │
 │                  ▼
 │              Claude 작업
 │                  │
 │                  ▼
 │              Baton / Evidence / Risks 업데이트
 │
 └──────────────▶ @codex
                    │
                    ▼
                Codex 수신검증 / 작업
```

---

## 27. 최종 결론

이 오케스트레이터는 Claude와 Codex를 번갈아 부르는 봇이 아니다.

AI 개발자들이 서로 일을 넘기기 전에 검증, 증거, 수락 절차를 강제하는 AGI 시대의 개발 현장소장이다.

핵심 3개:

```txt
1. Skill-Based
2. Evidence Gate
3. Baton Protocol
```
