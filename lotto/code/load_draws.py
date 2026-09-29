"""당첨번호 파일 로더 — 동행복권 형식 xlsx / 저장소 CSV 공용.

지원 형식
  xlsx : 회차, 당첨번호1~6, 보너스번호, 1등당첨수, 일등 당첨금액, 로또 총 구매금액, 발표일
         (예: data/lottowinnumber_20260929.xlsx)
  csv  : round,n1,n2,n3,n4,n5,n6,bonus,w1,prize1,sales,date
         (예: data/draws_1224_1243.csv — 위 xlsx 를 그대로 내보낸 것)

반환: {회차: dict(numbers=(6개 정렬 튜플), bonus, w1, prize1, sales, date)}
두 형식 모두 열 순서로만 읽는다. 헤더 이름은 확인하지 않는다.
"""
from __future__ import annotations
import csv
from pathlib import Path


def _row(cells):
    r = int(cells[0])
    nums = tuple(sorted(int(x) for x in cells[1:7]))
    bonus = int(cells[7])
    if len(set(nums)) != 6 or not (1 <= nums[0] and nums[-1] <= 45):
        raise ValueError(f'{r}회 본번호 오류: {nums}')
    if not (1 <= bonus <= 45) or bonus in nums:
        raise ValueError(f'{r}회 보너스 오류: {bonus}')
    opt = lambda i: int(cells[i]) if len(cells) > i and cells[i] not in (None, '') else None
    return r, dict(numbers=nums, bonus=bonus, w1=opt(8), prize1=opt(9), sales=opt(10),
                   date=str(cells[11]) if len(cells) > 11 and cells[11] is not None else None)


def load_draws(path):
    """xlsx 또는 csv 를 읽어 회차별 dict 로 반환. 첫 행은 헤더로 보고 건너뛴다."""
    path = Path(path)
    if path.suffix.lower() == '.xlsx':
        import openpyxl, warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')          # 동행복권 xlsx 는 기본 스타일이 없어 경고가 뜬다
            ws = openpyxl.load_workbook(path, read_only=True).active
        rows = [r for r in ws.iter_rows(values_only=True) if r and r[0] is not None]
    else:
        rows = [r for r in csv.reader(open(path, encoding='utf-8')) if r]
    out = {}
    for cells in rows[1:]:
        r, d = _row(cells)
        if r in out:
            raise ValueError(f'{r}회 중복')
        out[r] = d
    return out


def numbers_by_round(draws):
    """estimate_popularity.build_dataset 의 draws 인자 형식: {회차: 본번호 6개 튜플}"""
    return {r: d['numbers'] for r, d in draws.items()}


def sales_by_round(draws):
    """estimate_popularity.build_dataset 의 sales 인자 형식: {회차: 실측 총판매금액}"""
    return {r: d['sales'] for r, d in draws.items() if d['sales']}


if __name__ == '__main__':
    import sys
    for p in sys.argv[1:]:
        d = load_draws(p)
        print(f'{p}: {len(d)}회 ({min(d)}~{max(d)})')
        for r in sorted(d):
            x = d[r]
            print(f"{r}  {' '.join(f'{n:2d}' for n in x['numbers'])}  +{x['bonus']:2d}"
                  f"  1등 {x['w1']}게임  판매 {x['sales']}  {x['date']}")
