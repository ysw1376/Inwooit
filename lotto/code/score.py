#!/usr/bin/env python3
"""전달본 채점 — HANDOFF 8절 1단계.

사용
  python score.py --round 1244 --lines ../results/FINAL_POP35.json --draws ../data/lottowinnumber_20261003.xlsx
  python score.py --round 1244 --lines ../results/FINAL_POP35.json --winning 1,2,3,4,5,6 --bonus 7

--lines : "lines" 키를 가진 JSON (generate.py --out 산출물, FINAL_*.json) 또는
          한 줄에 번호 6개를 공백/쉼표로 적은 텍스트 파일
--draws : 당첨번호 xlsx/csv (load_draws 참조). 해당 회차가 없으면 오류
--winning/--bonus : 파일 대신 직접 입력

규칙: 직전 전달본만 채점한다. 결과를 보고 시드·컷·제약을 바꾸지 않는다.
"""
import argparse, json, re
from pathlib import Path
from lotto_core import rank, score_set, verify
from load_draws import load_draws


def load_lines(path):
    p = Path(path)
    if p.suffix.lower() == '.json':
        return [list(map(int, l)) for l in json.load(open(p))['lines']]
    lines = []
    for ln in open(p, encoding='utf-8'):
        nums = [int(x) for x in re.findall(r'\d+', ln)]
        if len(nums) == 6:
            lines.append(nums)
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--round', type=int, required=True)
    ap.add_argument('--lines', required=True)
    ap.add_argument('--draws')
    ap.add_argument('--winning')
    ap.add_argument('--bonus', type=int)
    a = ap.parse_args()

    if a.winning:
        winning = sorted(int(x) for x in re.findall(r'\d+', a.winning))
        bonus = a.bonus
    elif a.draws:
        d = load_draws(a.draws)
        if a.round not in d:
            raise SystemExit(f'{a.round}회가 {a.draws} 에 없다 (보유: {min(d)}~{max(d)})')
        winning, bonus = list(d[a.round]['numbers']), d[a.round]['bonus']
    else:
        raise SystemExit('--draws 또는 --winning 중 하나는 필요하다')
    if len(winning) != 6:
        raise SystemExit(f'당첨번호는 6개여야 한다: {winning}')

    lines = load_lines(a.lines)
    v = verify(lines)
    if not all(x for k, x in v.items() if k.endswith('ok') or k in ('n_lines', 'unique', 'sorted_valid')):
        print('경고: 전달본이 불변 조건을 위반한다', v)

    print(f"{a.round}회  당첨 {' '.join(f'{x:2d}' for x in winning)}  보너스 {bonus if bonus is not None else '?'}")
    print(f"전달본 {a.lines}  ({len(lines)}줄)")
    for i, l in enumerate(lines, 1):
        k = len(set(l) & set(winning)); rk = rank(l, winning, bonus)
        mark = ''.join('*' if x in winning else ' ' for x in l)
        tag = f'{rk}등' if isinstance(rk, int) and rk else ('5개 일치(보너스 미상)' if rk == 'unknown' else '')
        print(f"{i:2d}  " + "  ".join(f"{x:2d}" for x in l) + f"   일치 {k}  {tag}")
    s = score_set(lines, winning, bonus)
    ranks = {k: v for k, v in sorted(s['ranks'].items(), key=str) if k != 0}
    print(f"\n최다 일치 {s['best_match']}개  등수 {ranks or '낙첨'}  "
          f"4·5등 고정지급 {s['payout']:,}원  비용 {s['cost']:,}원  수지 {s['payout'] - s['cost']:+,}원")
    if 1 in s['ranks'] or 2 in s['ranks'] or 3 in s['ranks']:
        print("1~3등은 공동 분배라 금액을 여기서 확정하지 않는다.")


if __name__ == '__main__':
    main()
