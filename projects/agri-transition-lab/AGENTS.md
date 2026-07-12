# Codex 작업 지침

## 우선순위

1. `docs/IMPLEMENTATION_SPEC.md`
2. `docs/CALCULATION_SPEC.md`
3. `docs/DATA_SOURCE_REGISTRY.md`
4. 기존 테스트

## 금지

- 확인하지 않은 공식 API URL을 추정해 코드에 넣지 않는다.
- API 키를 프런트엔드에 포함하지 않는다.
- 흙토람 지도·VWorld 주소검색 결과를 저장·재배포하지 않는다.
- 비공식 사이트를 무단 크롤링하지 않는다.
- 신청 가능한 지원을 확정 지원으로 계산하지 않는다.
- 최근 5년 기후만으로 영구 적지를 판정하지 않는다.
- 사용자가 넣은 낙관값을 경고 없이 받아들이지 않는다.

## 완료 전 필수

```bash
npm test
npm run build
npm run validate:data
```

실행할 수 없는 명령은 이유와 미검증 범위를 PR에 기록한다.
