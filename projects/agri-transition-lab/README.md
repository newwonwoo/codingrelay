# 농업전환랩

기후·토양·특용작물·지원제도·사업성·실행절차를 한 프로젝트로 연결하는 귀농 의사결정 샌드박스입니다.

## 현재 상태

- 실행 가능한 React/TypeScript MVP
- 3개 지역·3개 작물 데모
- 적합도 하드컷과 신뢰도 분리
- 10년 현금흐름 계산
- 지원사업 상태 분리
- 공식 API 수집기 골격
- GitHub Actions CI/수집 워크플로

현재 seed 데이터는 기능 검증용입니다. 실제 추천에는 출처가 검증된 `public/data/v1` 스냅샷만 사용해야 합니다.

## 최초 전개

현재 브랜치의 `bootstrap.mjs`와 `scaffold.part00~03`은 검증 완료된 전체 프로젝트 번들입니다.

```bash
cd projects/agri-transition-lab
node bootstrap.mjs
npm install
npm test
npm run validate:data
npm run build
```

번들 SHA-256: `5483332221996739c322ec002594dd1759c1ac1c36b8f3618b81edc25a5de549`

## 문서

- `docs/IMPLEMENTATION_SPEC.md`: 전체 설계
- `docs/CODEX_EXECUTION_PLAN.md`: Codex PR 순서
- 번들 전개 후 추가 문서: 데이터 원천·사전·계산식·운영절차·API 어댑터

## 데이터 수집

실제 API 키는 `.env` 또는 GitHub Actions Secrets에만 둡니다. 운영 URL을 확인하지 않은 API는 추정해서 코드에 넣지 않습니다.
