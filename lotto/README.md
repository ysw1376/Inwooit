# 로또 6/45 분석 — Claude Code 인계 패키지

이 패키지 하나로 작업을 이어받는다. 먼저 `docs/HANDOFF.md` 를 읽어라.

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
docs/02_RESEARCH.md              번호별 인기도 1차 연구 (60회)
docs/03_RESEARCH_459.md          확대 분석 (459회) — 현재 근거
code/lotto_core.py               핵심 모듈 (생성·검증·채점·커버리지)
code/estimate_popularity.py      인기도 추정 + 시간분할 검증
code/generate.py                 회차별 25줄 생성 CLI
code/score.py                    전달본 채점 CLI (HANDOFF 8절 1단계)
code/load_draws.py               당첨번호 xlsx/csv 로더
data/tier_winners_784_1243.csv   등수별 당첨게임 수 459회
data/gamma_459.npy               추정된 번호별 인기도 (45개)
data/lottowinnumber_20260929.xlsx  동행복권 당첨번호 1224~1243회 (본번호·보너스·1등·실측 판매액)
data/draws_1224_1243.csv         위 xlsx 를 그대로 내보낸 CSV
results/*.json                   최종 번호·시뮬레이션 결과
```

## 빠른 시작

```bash
pip install numpy scipy openpyxl
cd code
# 직전 전달본 채점 (당첨번호 파일 또는 --winning/--bonus 직접 입력)
python score.py --round 1244 --lines ../results/FINAL_POP35.json --draws ../data/lottowinnumber_20261003.xlsx
# 다음 회차 생성
python generate.py --round 1245 --gamma ../data/gamma_459.npy
```

`generate.py --round 1244` 는 `results/FINAL_POP35.json` (시드 12442039) 을 그대로 재현한다
(2026-09-29 numpy 2.4 에서 확인). 재현이 깨지면 numpy 버전을 먼저 의심하라.

## 사용자가 매주 제공해야 할 것

| 자료 | 필수 | 출처 |
|---|---|---|
| 당첨번호 6개 + 보너스 | **필수** | 동행복권 |
| 등수별 당첨게임 수 (1~5등) | 권장 | https://lottohell.com/statistics/round-rank-winners/ |
| 총판매금액 | 선택 | 동행복권. 없으면 배분규칙으로 역산 |

등수별 당첨게임 수가 쌓일수록 인기도 추정이 정밀해진다. 없어도 번호 생성은 가능하다.

## 최초 1회 필요한 자료 (이미 사용자가 보유)

- `lotto.xlsx` — 1~1227회 본번호·보너스·1등/2등 당첨금·당첨게임수
- 1228회 이후 본번호·보너스 (대화로 전달)

## 절대 하지 말 것

- 과거 성적이 좋았던 시드를 사후에 고르기
- 결과를 본 뒤 필터·컷·제약 변경
- 워크포워드에서 나온 1등 사례를 성능 근거로 제시
- "적중률 N%" 를 예측력으로 표현
