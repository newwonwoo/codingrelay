# 농업전환랩 0원 MVP 구현명세 v1.0

## 1. 목표

귀농 예정자의 `지역→작물→지원→사업성→실행절차`를 한 프로젝트로 연결한다. 결과는 수익 보장이 아니라 근거·불확실성·탈락조건이 보이는 의사결정 지원이어야 한다.

## 2. 0원 범위

가능: 공개 GitHub, 공개 저장소 GitHub Actions, 정적 React 앱, 무료 공공 API 한도, 브라우저 IndexedDB/localStorage, JSON 스냅샷 커밋.

불가/주장 금지: 전국 상업 SaaS의 영구 0원 운영, 서버 DB·로그인·파일보관, 지자체 비정형 공고 100% 자동판독, 필지 미기후·배수·수원 확정, 농가수익 보장.

## 3. MVP

- 시범지역: 전남 해남, 경남 남해, 제주 서귀포
- 시범작물: 올리브, 페이조아, 패션프루트
- 화면: 지역·작물 / 사업성 / 지원제도 / 실행 로드맵 / 한 장 보고서
- 계산: 장기기후, 최근 5년 변화, 올해 단기위험, 적합도 하드컷, 10년 현금흐름, 보수·기준·낙관 시나리오

## 4. 아키텍처

```text
공식 API·공식 파일·수동검증
  → GitHub Actions Node.js 수집기
  → raw → normalized → derived
  → public/data/v1 정적 JSON
  → Vite+React 정적 앱
  → 사용자 입력은 브라우저 저장
```

서버 없이 핵심 계산이 동작해야 하며 API 장애 시 마지막 PASS 스냅샷을 유지한다.

## 5. 데이터 원천

| ID | 원천 | 방식 | 갱신 | 역할 |
|---|---|---|---|---|
| kma.asos.daily | 기상청 ASOS 일자료 | API | 일 | 30년/5년 기후 파생 |
| kma.vilage.forecast | 기상청 단기예보 | API | 일 | 72시간 영농위험 |
| kamis.price | KAMIS 가격 | API | 월 | 가격 기준·경고 |
| mois.benefits | 대한민국 공공서비스 혜택 | API | 주 | 지원사업 후보 |
| rda.income | 농진청 소득자료 | 공식 파일/수동 | 연 | 기준 단수·비용 |
| agrix.guide | AgriX 시행지침 | 수동구조화+링크 | 연 | 세부 자격·융자 |
| local.notice | 시군·농업기술센터 공고 | 시범지역 수동검증 | 주 | 실제 모집상태 |
| soil.manual | 흙토람/토양검정 | 사용자 입력 | 요청 | 배수·토심·pH |
| crop.profile | 농진청·논문·공식지침 | 검증 PR | 변경 시 | 희소작물 임계값 |

API가 명확하지 않은 원천을 임의 엔드포인트로 구현하지 않는다.

## 6. 수집기 공통 규칙

- timeout 15초
- retry 3회: 1초/3초/9초+jitter
- 재시도: 408,429,500,502,503,504, 네트워크 오류
- 인증·404·스키마 오류는 재시도 금지
- 원응답 checksum, 조회일, 기준기간, 행수, 결측률 기록
- 이전 성공보다 행수 30% 이상 감소하면 게시 중단
- 여러 페이지 중 하나라도 실패하면 새 스냅샷 게시 금지
- API 키 로그 마스킹

공통 manifest:

```json
{
  "sourceId":"kma.asos.daily",
  "schemaVersion":"1.0.0",
  "fetchedAt":"ISO8601",
  "periodStart":"YYYY-MM-DD",
  "periodEnd":"YYYY-MM-DD",
  "recordCount":0,
  "sourceUrl":"official",
  "license":"terms",
  "checksum":"sha256:...",
  "quality":{"status":"PASS","missingRate":0,"warnings":[]}
}
```

## 7. ASOS 어댑터

공식 안내: `https://www.data.go.kr/data/15059093/openapi.do`

요청: `https://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList`

필수 파라미터: `serviceKey,pageNo,numOfRows,dataType=JSON,dataCd=ASOS,dateCd=DAY,startDt,endDt,stnIds`.

필드: `tm,stnId,avgTa,minTa,maxTa,sumRn,sumSsHr,sumGsr,avgWs,maxWs,maxInsWs,avgRhm,minTg`.

정규화 키: `(stationId,date)`. 최근 3일을 재수집해 정정값을 반영한다.

파생:

```text
GDD = Σ max(0, 일평균 - 작물 기준온도)
서리일 = Tmin < 0
폭염일 = Tmax ≥ 33
집중강수일 = 강수 ≥ 80mm
무상기간 = 봄 마지막 서리 다음날~가을 첫 서리 전날
```

## 8. 단기예보 어댑터

공식 안내: `https://www.data.go.kr/data/15084084/openapi.do`

요청: `https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst`.

입력: `base_date,base_time,nx,ny`; TMP/TMN/TMX/POP/PCP/REH/WSD/SKY/PTY를 정규화한다. 단기예보는 장기 적지점수를 변경하지 않고 ‘올해 운영위험’만 표시한다.

## 9. KAMIS

공식 안내: `https://www.kamis.or.kr/customer/reference/openapi_list.do`

요청: `https://www.kamis.or.kr/service/price/xml.do?action=periodWholesaleProductList`.

가격은 품목·품종·시장·등급을 구분하고 월별 중앙값과 25/75백분위를 만든다. 도매가격을 농가수취가격과 동일시하지 않는다. 희소작물 미수록 시 공식 소득자료 또는 근거등급이 있는 수동값을 사용한다.

## 10. 정부혜택

공식 안내: `https://www.data.go.kr/data/15113968/openapi.do`.

활용신청 후 Swagger 운영 URL을 `BENEFITS_API_BASE_URL`에 저장한다. URL을 추정하지 않는다. 자동 응답으로 사업명·기관·내용·대상·신청방법·문의·원문을 모으고, 금액·자부담·상환·기간은 원문 수동검증 큐로 보낸다.

상태: `ELIGIBLE/POSSIBLE/BLOCKED/CLOSED/REFERENCE_ONLY`. 가능은 선정 확정이 아니다.

## 11. 토양

흙토람 지도타일을 복제·저장하지 않는다. 공식 조회링크와 입력가이드를 제공하고 배수, 토성, 유효토심, 경사, pH, EC, 유기물, 관수원, 염해노출을 입력받는다.

신뢰도: `OFFICIAL_REPORT > OFFICIAL_MAP > FIELD_CHECK > USER_ESTIMATE`. 사용자 추정만 있으면 토양점수 상한 60점.

## 12. 작물 프로필

API/AI로 임계값을 자동 생성하지 않는다. 프로필은 치사온도, 경고온도, GDD, 무상기간, 강수, 일조, 풍속, 토양, 연차별 수확계수, 단수, 상품화율, 가격범위, 조성비, 운영비, 노동시간과 출처를 가진다.

근거등급 A~D. D는 상업재배 1순위 추천 금지, C는 시험재배 우선.

## 13. 적합도

하드컷:

- 극저온이 치사온도 이하
- 무상기간 미달
- GDD가 최소의 85% 미만
- 배수 매우 불량
- 수원 필수인데 관수원 없음
- 가온 작물인데 시설 제외

```text
Agronomic = Climate 55 + Soil 30 + Disaster 15
Business = Profit 45 + Market 20 + Finance 20 + Operations 15
Recommendation = Agronomic×0.55 + Business×0.45
표시점수 = 원점수 × 데이터신뢰도
```

하드컷 실패는 점수와 무관하게 탈락.

## 14. 사업성

```text
10a = 평/302.5
생산량 = 10a×성목단수×연차수확계수
상품수량 = 생산량×상품화율×(1-재해손실)
매출 = 도매수량×농가수취가 + 직거래총액 - 포장·택배·수수료·반품
현금흐름 = 매출-현금운영비-이자-원금-추가투자
```

토지매입은 비용과 자산을 분리한다. 가족노동은 현금흐름과 기회비용을 각각 표시한다. 확정보조금만 기준안에 반영하고 신청예정은 별도 시나리오. 융자는 유입뿐 아니라 원리금상환도 반영한다.

결과: 초기투자, 최소자기자본, 최대현금부족, 손익분기연도, 회수연도, 5·10년 누적, 성목기소득, 손익분기 단수·가격, 보조금의존도.

## 15. 경고

- 자기자본 < 최대현금부족
- 예정보조금 의존
- 직거래 가격이 근거상단 120% 초과
- 상품화율 90% 초과
- 근거등급 C/D 단수
- 회수기간 10년 초과
- 가온 에너지비가 성목기 매출 25% 초과

## 16. 지원 매칭 입력

지역, 연령, 전입상태·일자, 영농경력, 교육시간, 경영체, 농지확보, 자기자본, 사업비, 작물·시설, 주거 필요.

## 17. 실행 게이트

G0 후보지역 → G1 현장검증 → G2 농지확보 → G3 자격·교육 → G4 자금조달 → G5 시설·인허가 → G6 시험재배 → G7 본재배 → G8 판매·가공 → G9 성과점검.

각 노드: 담당자, 선행조건, 문서, 비용, 마감, 공식출처, 사용자상태.

## 18. 개인정보·보안

로그인 없음. 프로젝트는 IndexedDB/localStorage. 주민번호·정확한 자산 식별정보 수집 금지. API 키는 GitHub Secrets. 주소좌표 결과 저장 금지.

## 19. Actions

- CI: test, data validation, build
- daily: ASOS 증분·예보
- weekly: 정부혜택·링크 검사
- monthly: KAMIS
- annual manual PR: 농림사업 지침·소득자료·작물 프로필
- 수집 실패 시 마지막 데이터 유지

## 20. 완료조건

Phase 0: React/TS, 3지역×3작물, 계산·적합도 테스트.
Phase 1: ASOS/예보 실데이터와 freshness.
Phase 2: KAMIS·10년 현금흐름·민감도.
Phase 3: 정부혜택·수동검증·자격룰.
Phase 4: 로드맵·인쇄보고서·JSON 백업.

모든 PR은 `npm test`, `npm run validate:data`, `npm run build`를 통과해야 한다.
