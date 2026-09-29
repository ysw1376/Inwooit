"""data/ 의 CSV만으로 estimate_popularity 가 요구하는 3개 사전을 만든다.

외부 파일(lotto.xlsx 등)에 의존하지 않는다. openpyxl 도 필요 없다.

    from load_inputs import load
    draws, prize2, sales = load()           # code/ 기준 기본 경로 ../data
    rows = build_dataset('../data/tier_winners_784_1243.csv', draws, prize2, sales)

반환값
  draws[r]  = (본번호 6개 오름차순 튜플)                      1 ~ 1243
  prize2[r] = (2등 1게임 금액, 2등 게임수, 1등 금액, 1등 게임수)  1 ~ 1243
  sales[r]  = 실측 총판매금액(원)                              1224 ~ 1243

출처
  draws_prizes_1_1227.csv     1 ~ 1227회. 사용자 제공 lotto.xlsx 를 그대로 옮긴 것.
                              1·2등 당첨금과 당첨게임수를 모두 가진 유일한 구간.
  draws_sales_1224_1243.csv   1224 ~ 1243회. 동행복권 공개 회차별 총판매금액.
                              2등 정보가 없어 prize2 의 앞 두 자리는 None 이다.

1228~1243 구간 — 2등 자료 없음, 영향은 감사 완료
  이 구간은 2등 상금풀(B2)을 직접 알 수 없다. 결과는 두 가지다.
    (1) 판매액을 역산하지 않고 실측 sales 를 그대로 쓴다. 이 편이 정확하다.
    (2) build_dataset 의 이월 회차 제외 규칙(B1/B2 > 6.01)이 B2=0 이라 건너뛰어진다.

  (2)가 실제로 문제를 일으켰는지는 배분 항등식으로 B2 를 복원해 확인했다.
    B2 = (S - 2*(50,000*W4 + 5,000*W5)) / 16
  2등 실측이 있는 1224~1227 에서 이 복원의 상대오차는 1.3e-08 이었고,
  1228~1243 열여섯 회차는 전부 B1/B2 = 6.000 (이월 아님)이었다.
  즉 빠진 판정이 걸러냈을 회차는 하나도 없고, gamma_459.npy 는 영향받지 않는다.
  verify_gamma.py 가 이 감사를 매번 다시 돌린다.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, os.pardir, 'data')


def _int(x):
    x = (x or '').strip()
    return int(x) if x else None


def load(data_dir=DATA):
    draws, prize2, sales = {}, {}, {}

    path = os.path.join(data_dir, 'draws_prizes_1_1227.csv')
    with open(path, newline='') as f:
        for d in csv.DictReader(f):
            r = int(d['round'])
            draws[r] = tuple(sorted(int(d[f'n{i}']) for i in range(1, 7)))
            prize2[r] = (_int(d['prize2']), _int(d['count2']),
                         _int(d['prize1']), _int(d['count1']))

    path = os.path.join(data_dir, 'draws_sales_1224_1243.csv')
    with open(path, newline='') as f:
        for d in csv.DictReader(f):
            r = int(d['round'])
            nums = tuple(sorted(int(d[f'n{i}']) for i in range(1, 7)))
            if r in draws and draws[r] != nums:      # 두 출처 교차검증
                raise ValueError(f'{r}회 본번호 불일치: {draws[r]} vs {nums}')
            draws[r] = nums
            sales[r] = int(d['sales'])
            if r not in prize2:                       # 1228~1243: 2등 자료 없음
                prize2[r] = (None, None, _int(d['prize1']), _int(d['count1']))

    return draws, prize2, sales


if __name__ == '__main__':
    draws, prize2, sales = load()
    print(f'draws  {len(draws)}회  {min(draws)}~{max(draws)}')
    print(f'prize2 {len(prize2)}회  2등자료 보유 '
          f'{sum(1 for v in prize2.values() if v[0] is not None)}회')
    print(f'sales  {len(sales)}회  {min(sales)}~{max(sales)}')
