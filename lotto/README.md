# 로또 6/45 분석 — Claude Code 인계 패키지

이 패키지 하나로 작업을 이어받는다. 외부 파일이 더 필요하지 않다.

읽는 순서: `docs/HANDOFF.md` → `results/DELIVERY.md`.
앞은 방법론 전체, 뒤는 **지금 어느 25줄이 전달본인지**를 정하는 유일한 기준이다.

## 이 작업의 성격 — 먼저 확인할 것

**당첨번호를 예측하지 않는다.** 과거 빈도·이월·전이로 다음 번호를 좁히는 시도는
1회차부터 워크포워드로 전부 검정되어 기각됐다(`docs/HANDOFF.md` 4절).

확정된 것은 두 가지뿐이다.
1. **조합 배치 최적화** — 25줄을 겹치지 않게 펼쳐 "최소 한 줄 당첨" 확률을 올린다 (결정론적)
2. **구매 인기도 회피** — 사람들이 덜 사는 조합을 골라 당첨 시 분배 몫을 키운다 (통계 모형, 검증됨)

**1등 확률 25/8,145,060 은 어느 방법으로도 달라지지 않는다.**

## 구조

```
README.md                        이 파일
docs/HANDOFF.md                  전체 인계 문서 — 반드시 먼저 읽을 것
docs/00_PREREG.md                인기도 검정 사전 등록 (데이터 수집 전 작성)
docs/01_RESULTS.md               확증 검정 결과 (40회)
docs/02_RESEARCH.md              번호별 인기도 1차 연구 (60회) — 작성 시점 기록
docs/03_RESEARCH_459.md          확대 분석 (459회) — 현재 근거
code/lotto_core.py               핵심 모듈 (생성·검증·채점·커버리지)
code/load_inputs.py              data/ CSV -> draws·prize2·sales 사전
code/estimate_popularity.py      인기도 추정 + 시간분할 검증
code/verify_gamma.py             gamma_459.npy 재현 검증 (비트 대조)
code/generate.py                 회차별 25줄 생성 CLI
code/score.py                    전달본 채점 (purchased 미기입 시 중단)
data/draws_prizes_1_1227.csv     1~1227회 본번호·보너스·1·2등 당첨금/게임수
data/draws_sales_1224_1243.csv   1224~1243회 본번호·보너스·1등·실측 총판매금액
data/tier_winners_784_1243.csv   등수별 당첨게임 수 459회
data/gamma_459.npy               추정된 번호별 인기도 (45개)
data/lotto.xlsx                  위 CSV의 원본 (사용자 제공, 보존용)
data/lottowinnumber_1224_1243.xlsx  판매금액 원본 (보존용)
results/DELIVERY.md              1244회 전달본 기준 문서 — 두 번째로 읽을 것
results/delivery.json            전달본 registry (purchased 필드가 실적 기준)
results/*.json                   최종 번호·시뮬레이션 결과
```

## 빠른 시작

```bash
pip install numpy scipy
cd code
python verify_gamma.py                                    # 재현 검증 (통과해야 함)
python generate.py --round 1245 --gamma ../data/gamma_459.npy
python score.py --winning 3 9 14 22 30 41 --bonus 7       # 추첨 후
```

`openpyxl` 은 CSV만 쓰면 필요 없다. `data/*.xlsx` 를 직접 열 때만 설치한다.

## 사용자가 매주 제공해야 할 것

| 자료 | 필수 | 출처 |
|---|---|---|
| 당첨번호 6개 + 보너스 | **필수** | 동행복권 |
| 등수별 당첨게임 수 (1~5등) | 권장 | https://lottohell.com/statistics/round-rank-winners/ |
| 총판매금액 | 선택 | 동행복권. 없으면 배분규칙으로 역산 |

등수별 당첨게임 수가 쌓일수록 인기도 추정이 정밀해진다. 없어도 번호 생성은 가능하다.

## 최초 1회 필요한 자료 — 이미 패키지 안에 있다

`data/draws_prizes_1_1227.csv`(1~1227회)와 `data/draws_sales_1224_1243.csv`(1224~1243회)가
1~1243회 전 회차의 본번호·보너스와 인기도 추정에 필요한 금액 자료를 모두 담는다.
원본 엑셀도 `data/` 에 보존해 두었다. `python code/verify_gamma.py` 가 통과하면
`gamma_459.npy` 를 이 CSV만으로 비트 단위까지 재현할 수 있다는 뜻이다.

1228~1243회 구간은 2등 상금풀 자료가 없어 이월 회차 제외 규칙이 작동하지 않는다.
실측 판매금액을 쓰므로 판매액 자체는 오히려 더 정확하다. 자세한 건
`code/load_inputs.py` 의 docstring 을 본다.

## 절대 하지 말 것

- 과거 성적이 좋았던 시드를 사후에 고르기
- **추첨 결과를 본 뒤 `delivery.json` 의 `purchased` 를 정하기**
- 결과를 본 뒤 필터·컷·제약 변경
- 워크포워드에서 나온 1등 사례를 성능 근거로 제시
- "적중률 N%" 를 예측력으로 표현
- `FINAL_POP35.json` 과 `FINAL_1244.json` 의 `mult` 필드를 나란히 비교하기
  (서로 다른 인기도 모형의 산출값이다 — `results/DELIVERY.md` 2절)
