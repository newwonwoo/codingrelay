# 농업전환랩

기후·토양·특용작물·지원제도·사업성·실행절차를 한 프로젝트로 연결하는 귀농 의사결정 샌드박스입니다.

## 현재 브랜치 상태

- 0원 개인검증용 구현명세
- 데이터 수집 최하위 규칙
- 단계별 Codex 실행계획
- React/TypeScript 작업공간 초기화

완성·검증된 전체 로컬 scaffold는 별도 산출물로 보관하고, GitHub에서는 Codex가 PR-01부터 작은 변경 단위로 구현하도록 진행합니다. 현재 브랜치를 완성 앱으로 오해하면 안 됩니다.

## Codex 시작 순서

```bash
cd projects/agri-transition-lab
cat AGENTS.md
cat docs/IMPLEMENTATION_SPEC.md
cat docs/CODEX_EXECUTION_PLAN.md
npm install
```

이후 PR-01의 기반·계산엔진부터 구현합니다.

## 데이터 원칙

현재 작성될 seed 값은 기능 검증용입니다. 실제 추천에는 출처가 검증된 `public/data/v1` 스냅샷만 사용해야 합니다. 실제 API 키는 `.env` 또는 GitHub Actions Secrets에만 두며, 운영 URL을 확인하지 않은 API는 추정해서 코드에 넣지 않습니다.
