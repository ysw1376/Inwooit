"""전달본 채점. results/delivery.json 의 purchased 필드만 실적으로 인정한다.

    python score.py --winning 3 9 14 22 30 41 --bonus 7
    python score.py --winning ... --bonus 7 --all      # 후보 전 세트를 참고로 함께 출력
    python score.py --winning ... --bonus 7 --registry ../results/delivery_1245.json

규칙 (HANDOFF 8절)
  - 직전 전달본만 채점한다. 실제로 구매한 세트가 무엇인지 registry 의 purchased 에
    적혀 있어야 한다. 비어 있으면 중단한다 — 사후에 성적 좋은 세트를 고를 여지를 없앤다.
  - --all 은 참고 출력일 뿐이며, 실적 기록(HANDOFF 9절)에는 purchased 세트만 올린다.
  - 다른 AI가 준 번호의 성적과 합산하지 않는다.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lotto_core import score_set, rank            # noqa: E402

DEFAULT_REG = os.path.join(HERE, os.pardir, 'results', 'delivery.json')
TIER_NAME = {1: '1등', 2: '2등', 3: '3등', 4: '4등', 5: '5등'}


def read_winning(path):
    """회차 한 줄이 적힌 파일에서 본번호 6개와 보너스를 읽는다.
    '1244,3,9,14,22,30,41,7' 또는 '3 9 14 22 30 41 + 7' 형식 모두 허용."""
    txt = open(path).read().replace('+', ' ').replace(',', ' ').split()
    nums = [int(x) for x in txt]
    if len(nums) == 8:                 # 앞에 회차가 붙은 경우
        nums = nums[1:]
    if len(nums) not in (6, 7):
        raise SystemExit(f'{path}: 숫자 6개(+보너스) 여야 한다 — {len(nums)}개 읽음')
    return nums[:6], (nums[6] if len(nums) == 7 else None)


def report(name, info, winning, bonus, tag):
    s = score_set(info['lines'], winning, bonus)
    hits = {i: len(set(l) & set(winning)) for i, l in enumerate(info['lines'], 1)}
    print(f'\n[{tag}] {name}  시드 {info["seed"]}')
    won = [(i, info['lines'][i - 1], rank(info['lines'][i - 1], winning, bonus))
           for i in sorted(hits) if hits[i] >= 3]
    if won:
        for i, line, r in won:
            marked = ' '.join(f'*{n}*' if n in winning else
                              (f'({n})' if bonus is not None and n == bonus else str(n))
                              for n in line)
            print(f'  {i:2d}줄  {marked}   {TIER_NAME.get(r, r)}')
    else:
        print('  3개 이상 맞은 줄 없음')
    tiers = ' '.join(f'{TIER_NAME[k]} {s["ranks"][k]}줄'
                     for k in (1, 2, 3, 4, 5) if s['ranks'].get(k))
    print(f'  최고 일치 {s["best_match"]}개 | {tiers or "당첨 없음"}')
    print(f'  고정분 수령 {s["payout"]:,}원 / 구입 {s["cost"]:,}원 '
          f'= 수지 {s["payout"] - s["cost"]:+,}원  (1~3등 분배금 제외)')
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--winning', nargs=6, type=int, help='본번호 6개')
    ap.add_argument('--bonus', type=int, default=None)
    ap.add_argument('--file', help='당첨번호가 적힌 파일')
    ap.add_argument('--registry', default=DEFAULT_REG)
    ap.add_argument('--all', action='store_true',
                    help='구매하지 않은 후보 세트도 참고로 채점')
    a = ap.parse_args()

    if a.file:
        winning, bonus = read_winning(a.file)
        if a.bonus is not None:
            bonus = a.bonus
    elif a.winning:
        winning, bonus = a.winning, a.bonus
    else:
        raise SystemExit('--winning 6개 또는 --file 이 필요하다')
    if len(set(winning)) != 6 or not all(1 <= n <= 45 for n in winning):
        raise SystemExit(f'본번호가 잘못됐다: {winning}')

    reg = json.load(open(a.registry, encoding='utf-8'))
    print(f'{reg["round"]}회 ({reg.get("draw_date", "?")})  '
          f'당첨 {" ".join(map(str, sorted(winning)))}  보너스 {bonus}')

    bought = reg.get('purchased')
    if not bought:
        print(f'\n중단: {os.path.relpath(a.registry, HERE)} 의 "purchased" 가 비어 있다.')
        print('실제로 구매한 세트 이름을 적은 뒤 다시 실행한다. 후보:',
              ', '.join(reg['sets']))
        print('결과를 보고 세트를 고르면 실적 기록이 무의미해진다.')
        return 2
    if bought not in reg['sets']:
        raise SystemExit(f'purchased="{bought}" 가 sets 에 없다: {list(reg["sets"])}')

    s = report(bought, reg['sets'][bought], winning, bonus, '구매·실적')
    if a.all:
        for nm, info in reg['sets'].items():
            if nm != bought:
                report(nm, info, winning, bonus, '참고 — 실적 아님')
        print('\n참고 세트는 HANDOFF 9절 실적표에 올리지 않는다.')

    if 'unknown' in s['ranks']:
        print('\n보너스를 몰라 5개 일치의 2등/3등 판정을 보류했다. --bonus 를 주면 확정된다.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
