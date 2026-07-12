# Codex 실행계획

## 목표

`projects/agri-transition-lab`에 0원 개인검증용 MVP를 구현한다. 정적 앱, GitHub Actions 데이터 수집, 출처 추적, 사업성·적합도 테스트가 핵심이다.

## 작업 원칙

1. `AGENTS.md`와 `docs/IMPLEMENTATION_SPEC.md`를 먼저 읽는다.
2. 한 PR에 한 단계만 구현한다.
3. 공식 API 엔드포인트를 추정하지 않는다.
4. 실제 키가 없으면 fixture로 테스트한다.
5. 비공식 스크래핑을 추가하지 않는다.
6. 토양지도·주소결과를 무단 저장하지 않는다.
7. 모든 파생값에 출처·기준기간·신뢰도를 연결한다.

## PR 순서

### PR-01 기반과 계산엔진

- Vite React TypeScript
- 화면 5개
- 3지역×3작물 seed
- 적합도 하드컷
- 10년 현금흐름
- Vitest

완료: `npm test`, `npm run build`, `npm run validate:data` 통과.

### PR-02 KMA 수집

- ASOS collector
- pagination/retry/checksum
- fixture test
- climate feature builder
- 단기예보 위험
- daily workflow

완료: 키 없이 fixture, 키가 있으면 시범지역 스냅샷, 실패 시 마지막 스냅샷 유지.

### PR-03 KAMIS와 경제성

- 월별 가격수집
- 품목코드 매핑
- 중앙값·범위
- 가격 낙관 경고
- 보수/기준/낙관 병렬 계산

### PR-04 지원사업

- 정부혜택 generic adapter
- `BENEFITS_API_BASE_URL` 환경변수
- support schema
- 수동 검증 큐
- 자격 룰
- 확정/예정/참고 분리

### PR-05 실행계획

- 행위주체별 스윔레인
- 문서 체크리스트
- JSON 저장/복원
- 인쇄 CSS

### PR-06 데이터 품질·배포

- manifest UI
- stale 경고
- CI/Actions
- 개인검증용 정적 배포

## 검증 프롬프트

```text
IMPLEMENTATION_SPEC.md의 완료조건으로 변경사항을 검증하라.
1. 실제 공식 데이터가 아닌 값을 production 데이터처럼 표시하지 않았는가?
2. API 키가 클라이언트에 포함되지 않았는가?
3. 수집 실패 시 이전 스냅샷을 보존하는가?
4. 농업적합도와 사업성을 분리했는가?
5. 확정보조금과 신청예정을 분리했는가?
6. 계산식에 단위테스트가 있는가?
7. npm test, npm run validate:data, npm run build가 통과하는가?
PASS 또는 BLOCK으로 증거 파일과 남은 위험을 보고하라.
```
