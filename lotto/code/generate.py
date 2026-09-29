#!/usr/bin/env python3
"""회차별 25줄 생성 — U25_L1_POP35

규칙 (사전 고정, 결과 보고 변경 금지):
  후보  : 추정 인기도 하위 35%
  제약  : 모든 줄 쌍 공통 <= 1, 번호당 사용 <= 5
  시드  : round*10000+2026 부터 60개 탐색, 5등↑ 커버리지 최대 (동률 시 큰 시드)
  실패  : 오류로 중단. 시드·제약을 완화하지 않는다.

사용:  python generate.py --round 1245 --gamma ../data/gamma_459.npy
"""
import argparse, json
import numpy as np
from lotto_core import all_combos, popularity_pool, build, coverage, top2_probability, \
                       share_multiplier, verify, M

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--round', type=int, required=True)
    ap.add_argument('--gamma', default='../data/gamma_459.npy')
    ap.add_argument('--cut', type=int, default=35)
    ap.add_argument('--seeds', type=int, default=60)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()

    C, Cm = all_combos()
    g = np.load(a.gamma)
    pool, _ = popularity_pool(C, g, a.cut)
    base = a.round * 10000 + 2026
    best = None
    for i in range(a.seeds):
        sel, masks = build(pool, base + i, Cm, C)
        if sel is None:
            continue
        cov = coverage(masks, Cm)
        if best is None or (cov[3], base + i) > (best[0][3], best[1]):
            best = (cov, base + i, sel)
    if best is None:
        raise SystemExit('25줄 생성 실패 — 시드·제약을 바꾸지 말고 원인을 조사하라')
    cov, seed, sel = best
    lines = [sorted(int(x) for x in C[i]) for i in sel]
    out = dict(rule='U25_L1_POP35', target=a.round, cut=a.cut, seed=seed,
               coverage=cov, top2=top2_probability(lines),
               share_multiplier=share_multiplier(sel, g, C),
               verification=verify(lines), lines=lines)
    print(json.dumps({k: v for k, v in out.items() if k != 'lines'},
                     ensure_ascii=False, indent=1))
    for i, l in enumerate(lines, 1):
        print(f"{i:2d}  " + "  ".join(f"{x:2d}" for x in l))
    if a.out:
        json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
