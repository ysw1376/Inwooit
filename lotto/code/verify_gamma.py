"""data/ 의 CSV만으로 gamma_459.npy 를 재현하고 비트 단위로 대조한다.

    cd code && python verify_gamma.py

통과 기준
  - 표본 459회 (784~1243 중 결손·이월 제외)
  - 회차 오름차순으로 적합한 감마가 gamma_459.npy 와 비트 동일
  - number_popularity.csv 가 gamma_459.npy 와 1e-6 이내 (CSV는 소수 6자리 반올림)

  - 1228~1243 이월 감사: 배분 항등식으로 2등 상금풀을 복원해 이월 회차가 없음을 확인

행 순서 주의
  build_dataset 은 tier_winners CSV 에 적힌 순서 그대로 행을 만든다.
  동봉한 tier_winners_784_1243.csv 는 내림차순이라, 정렬 없이 적합하면
  부동소수점 누산 순서 때문에 감마가 최대 9.4e-17 (상대 5.1e-14) 어긋난다.
  수학적으로는 같은 값이지만 비트 동일은 아니다. 재현 검증에는 오름차순을 쓴다.
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, os.pardir, 'data')
sys.path.insert(0, HERE)

from load_inputs import load                       # noqa: E402
from estimate_popularity import build_dataset, fit_gamma   # noqa: E402

EXPECTED_N = 459
LAM = 1.0
CARRYOVER_RATIO = 6.01      # B1/B2 가 이보다 크면 이월 회차


def carryover_audit(prize2, sales, tier_csv):
    """1228~1243 은 2등 자료가 없어 이월 판정이 꺼져 있다. 항등식으로 복원해 감사한다.

        S = 16*B2 + 2*(50,000*W4 + 5,000*W5)   ->   B2 = (S - 2*(...)) / 16

    2등 실측이 있는 1224~1227 에서 복원 정확도를 먼저 확인한 뒤 적용한다.
    """
    tiers = {}
    with open(tier_csv, newline='') as f:
        for p in csv.reader(f):
            p = [int(x) for x in p]
            if sum(p[1:]) > 0:
                tiers[p[0]] = p[1:]

    def b2_hat(r):
        w4, w5 = tiers[r][3], tiers[r][4]        # [1등,2등,3등,4등,5등] 게임 수
        return (sales[r] - 2 * (50_000 * w4 + 5_000 * w5)) / 16

    err = []
    for r in (1224, 1225, 1226, 1227):
        if r in sales and prize2.get(r, (None,))[0]:
            a2, n2, _, _ = prize2[r]
            err.append(abs(b2_hat(r) - a2 * n2) / (a2 * n2))
    flagged = [r for r in range(1228, 1244)
               if r in sales and r in tiers
               and prize2[r][2] and prize2[r][3]
               and b2_hat(r) > 0
               and prize2[r][2] * prize2[r][3] / b2_hat(r) > CARRYOVER_RATIO]
    return (max(err) if err else None), flagged


def main():
    draws, prize2, sales = load(DATA)
    rows = build_dataset(os.path.join(DATA, 'tier_winners_784_1243.csv'),
                         draws, prize2, sales)
    rounds = sorted(r for r, _, _ in rows)
    ok = True

    print(f'표본 {len(rows)}회  {rounds[0]}~{rounds[-1]}', end='  ')
    if len(rows) != EXPECTED_N:
        print(f'[실패] {EXPECTED_N}회여야 한다'); ok = False
    else:
        print('[통과]')

    ref = np.load(os.path.join(DATA, 'gamma_459.npy'))
    g, _, _ = fit_gamma(sorted(rows, key=lambda x: x[0]), lam=LAM)
    same = np.array_equal(g, ref)
    print(f'gamma 재현  최대 절대차 {np.abs(g - ref).max():.3e}  '
          f'비트동일 {same}  [{"통과" if same else "실패"}]')
    ok &= same

    with open(os.path.join(DATA, 'number_popularity.csv'), newline='') as f:
        tbl = {int(p[0]): float(p[1]) for p in list(csv.reader(f))[1:]}
    d = max(abs(tbl[i + 1] - ref[i]) for i in range(45))
    print(f'number_popularity.csv 대조  최대차 {d:.3e}  '
          f'[{"통과" if d < 1e-6 else "실패"}]')
    ok &= d < 1e-6

    rel, flagged = carryover_audit(
        prize2, sales, os.path.join(DATA, 'tier_winners_784_1243.csv'))
    print(f'1228~1243 이월 감사  항등식 복원 상대오차 {rel:.1e} '
          f'(1224~1227 실측 대조) | 이월 회차 '
          f'{flagged if flagged else "없음"}  '
          f'[{"통과" if not flagged else "감마 재적합 필요"}]')
    ok &= not flagged

    order = np.argsort(-ref)
    print('인기 상위12 ' + ' '.join(str(i + 1) for i in order[:12]))
    print('인기 하위12 ' + ' '.join(str(i + 1) for i in order[-12:]))

    print('\n' + ('전체 통과' if ok else '실패 항목 있음 — 숫자를 맞추지 말고 원인을 보고할 것'))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
