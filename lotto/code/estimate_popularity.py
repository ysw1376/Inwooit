"""번호별 구매 인기도 추정 + 검증.

입력 (data/):
  tier_winners_*.csv  : round,1등,2등,3등,4등,5등  (등수별 당첨게임 수)
  lotto.xlsx          : 사용자 제공. 1~1227회 본번호 + 1·2등 당첨금/당첨게임수
  sales.xlsx (선택)   : 최근 회차 실측 총판매금액

판매액이 없으면 배분 규칙으로 역산: S = 16*B2 + 2*(50,000*W4 + 5,000*W5)
  (실측과 대조 시 원 단위 반올림으로 최대 1,000원 차이)
"""
import csv, math, sys
import numpy as np
from scipy import stats
from lotto_core import M, P3

def build_dataset(tier_csv, draws, prize2, sales=None):
    """draws[r] = (본번호 6개 튜플); prize2[r] = (2등 1게임 금액, 2등 게임수, 1등금액, 1등게임수)"""
    rows = []
    for p in csv.reader(open(tier_csv)):
        r = int(p[0]); c1, c2, c3, w4, w5 = map(int, p[1:6])
        if c1 + c2 + c3 + w4 + w5 == 0:        # 원자료 결손
            continue
        if r not in draws or r not in prize2:
            continue
        a2, n2, a1, n1 = prize2[r]
        if n1 is not None and c1 != n1:         # 출처 교차검증
            continue
        B2 = (a2 or 0) * (n2 or 0); B1 = (a1 or 0) * (n1 or 0)
        if n1 and B2 and B1 / B2 > 6.01:        # 이월 배당 제외
            continue
        S = sales.get(r) if sales and r in sales else (
            16 * B2 + 2 * (50_000 * w4 + 5_000 * w5) if B2 else 0)
        if S <= 0:
            continue
        rows.append((r, draws[r], w5 / (S / 1000) / P3))
    return rows


def fit_gamma(rows, lam=1.0, mask=None):
    """릿지: Z = a + sum_j gamma_j * 1(번호 j 추첨). gamma_j>0 = 인기 있는 번호."""
    Z = np.array([x[2] for x in rows]); n = len(Z)
    X = np.zeros((n, 45))
    for i, (_, s, _) in enumerate(rows):
        for v in s: X[i, v - 1] = 1
    m = np.ones(n, bool) if mask is None else mask
    Xm = X[m] - X[m].mean(0); Zm = Z[m] - Z[m].mean()
    return np.linalg.solve(Xm.T @ Xm + lam * np.eye(45), Xm.T @ Zm), X, Z


def validate(rows, split_round, lam=1.0):
    """시간 분할 검증. 앞 구간으로 적합, 뒤 구간 예측 R²."""
    R = np.array([x[0] for x in rows])
    tr, te = R <= split_round, R > split_round
    g, X, Z = fit_gamma(rows, lam, tr)
    pred = Z[tr].mean() + (X[te] - X[tr].mean(0)) @ g
    r2 = 1 - ((Z[te] - pred) ** 2).sum() / ((Z[te] - Z[te].mean()) ** 2).sum()
    sc = np.array([g[np.array(s) - 1].sum() for _, s, _ in rows])
    reg = stats.linregress(sc[te], Z[te])
    return dict(r2=float(r2), n_train=int(tr.sum()), n_test=int(te.sum()),
                slope=float(reg.slope), t=float(reg.slope / reg.stderr),
                p=float(reg.pvalue), r=float(reg.rvalue))
