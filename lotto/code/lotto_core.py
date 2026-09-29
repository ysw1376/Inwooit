"""로또 6/45 — 핵심 모듈. 생성·검증·채점·인기도 추정.

전제: 이 코드는 당첨번호를 예측하지 않는다. 두 가지만 한다.
  1) 25줄을 조합공간에 겹치지 않게 배치 (결정론적 최적화)
  2) 구매 인기도가 낮은 조합 선택 (검증된 통계 모형)
1등 확률 25/C(45,6) 는 어느 방법으로도 달라지지 않는다.
"""
from __future__ import annotations
import itertools, math
import numpy as np

M = math.comb(45, 6)                     # 8,145,060
P3 = math.comb(6, 3) * math.comb(39, 3) / M   # 한 줄이 정확히 3개 맞을 확률
ATTEN = 0.5 - 1/13                       # 5등 티켓의 저번호 기대치 기울기 = 11/26


def all_combos():
    """전 조합 배열과 비트마스크. 사전식 순서 — 재현에 필수."""
    C = np.fromiter(itertools.chain.from_iterable(
            itertools.combinations(range(1, 46), 6)),
        dtype=np.int8, count=M * 6).reshape(M, 6)
    Cm = np.zeros(M, np.int64)
    for i in range(6):
        Cm |= np.int64(1) << (C[:, i].astype(np.int64) - 1)
    return C, Cm


def popularity_pool(C, gamma, cut_pct=35):
    """추정 인기도 하위 cut_pct% 조합의 인덱스."""
    score = gamma[C - 1].sum(1)
    return np.where(score <= np.percentile(score, cut_pct))[0], score


def build(pool, seed, Cm, C, max_overlap=1, cap=5, n_lines=25):
    """균등 순회 + 겹침·사용횟수 제약. 실패 시 None (시드·제약 변경 금지)."""
    rng = np.random.default_rng(seed)
    sel, masks, use = [], [], np.zeros(46, int)
    for idx in rng.permutation(pool):
        m, nums = int(Cm[idx]), C[idx]
        if any(use[n] >= cap for n in nums):
            continue
        if any((m & s).bit_count() > max_overlap for s in masks):
            continue
        sel.append(int(idx)); masks.append(m); use[nums] += 1
        if len(sel) == n_lines:
            return sel, masks
    return None, None


def coverage(masks, Cm):
    """전수 대조: 최소 한 줄이 k개 이상 맞을 확률 (k=3,4,5)."""
    best = np.zeros(M, np.uint8)
    for m in masks:
        np.maximum(best, np.bitwise_count(Cm & np.int64(m)).astype(np.uint8), out=best)
    return {k: float((best >= k).mean()) for k in (3, 4, 5)}


def top2_probability(lines):
    """1등 또는 2등 확률. 모든 줄 쌍 공통<=4 면 상한 25*7/M 달성."""
    seven = {tuple(sorted(l + [n])) for l in lines for n in range(1, 46) if n not in l}
    return 7 * len(seven) / (M * 39)


def share_multiplier(sel, gamma, C):
    """전체 균등 추출 대비 기대 분배 몫 배수. 모델 가정에 의존 — docs 참조."""
    st = gamma[C - 1].sum(1) / ATTEN
    w = np.exp(-(st - st.mean()))
    return float(w[sel].mean() / w.mean())


def verify(lines, max_overlap=1, cap=5):
    """불변 조건 검증. 모든 항목이 True 여야 한다."""
    import collections
    u = collections.Counter(n for l in lines for n in l)
    mx = max(len(set(a) & set(b)) for a, b in itertools.combinations(lines, 2))
    return dict(
        n_lines=len(lines) == 25,
        unique=len({tuple(sorted(l)) for l in lines}) == 25,
        sorted_valid=all(sorted(l) == list(l) and len(set(l)) == 6
                         and 1 <= min(l) and max(l) <= 45 for l in lines),
        max_overlap_ok=mx <= max_overlap, max_overlap=mx,
        usage_ok=max(u.values()) <= cap, usage=(min(u.values()), max(u.values())),
        numbers_used=len(u),
    )


def rank(line, winning, bonus):
    """등수 판정. 보너스 미상(None)이면 5개 일치는 'unknown'."""
    s = set(line); k = len(s & set(winning))
    if k == 6: return 1
    if k == 5:
        if bonus is None: return 'unknown'
        return 2 if bonus in s else 3
    if k == 4: return 4
    if k == 3: return 5
    return 0


def score_set(lines, winning, bonus):
    """세트 채점. 4등 50,000원 / 5등 5,000원 고정."""
    import collections
    r = collections.Counter(rank(l, winning, bonus) for l in lines)
    best = max(len(set(l) & set(winning)) for l in lines)
    payout = r[4] * 50_000 + r[5] * 5_000
    return dict(ranks=dict(r), best_match=best, payout=payout, cost=len(lines) * 1000)
