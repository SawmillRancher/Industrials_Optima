"""ODFL work-day calendar: weekdays less New Year, Memorial Day, Independence Day, Labor Day, Thanksgiving + the Friday after,
Christmas Eve and Christmas (observed). Reproduces every work-day count published in the 2019-2026 releases."""
import datetime as dt
def _nth(y, m, wd, n):
    d = dt.date(y, m, 1); c = 0
    while True:
        if d.weekday() == wd:
            c += 1
            if c == n: return d
        d += dt.timedelta(1)
def _last(y, m, wd):
    d = (dt.date(y, m + 1, 1) if m < 12 else dt.date(y + 1, 1, 1)) - dt.timedelta(1)
    while d.weekday() != wd: d -= dt.timedelta(1)
    return d
def _obs(d): return d - dt.timedelta(1) if d.weekday() == 5 else (d + dt.timedelta(1) if d.weekday() == 6 else d)
def holidays(y):
    xmas = _obs(dt.date(y, 12, 25)); tg = _nth(y, 11, 3, 4)
    h = {_obs(dt.date(y, 1, 1)), _last(y, 5, 0), _obs(dt.date(y, 7, 4)), _nth(y, 9, 0, 1), tg, tg + dt.timedelta(1), xmas,
         xmas - dt.timedelta(1) if xmas.weekday() > 0 else xmas - dt.timedelta(3)}
    if dt.date(y + 1, 1, 1).weekday() == 5: h.add(dt.date(y, 12, 31))
    return h
def work_days(start, end):
    H = holidays(start.year) | holidays(end.year); n = 0; d = start
    while d < end:
        if d.weekday() < 5 and d not in H: n += 1
        d += dt.timedelta(1)
    return n
def quarter(y, q): return work_days(dt.date(y, 3 * q - 2, 1), dt.date(y + (q == 4), (3 * q) % 12 + 1, 1))
def year(y): return work_days(dt.date(y, 1, 1), dt.date(y + 1, 1, 1))
if __name__ == '__main__':
    print({f'Q{q}/26': quarter(2026, q) for q in (1, 2, 3, 4)}, {y: year(y) for y in range(2024, 2031)})
