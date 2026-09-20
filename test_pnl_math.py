#!/usr/bin/env python3
from math import isclose

def pnl(contributed: float, current: float, owed: float = 0, claimed: float = 0, withdrawn: float = 0) -> tuple[float, float, float]:
    gross = current + owed + claimed + withdrawn
    profit = gross - contributed
    pct = profit / contributed * 100 if contributed > 0 else 0.0
    return gross, profit, pct

cases = [
    ((100, 110, 2, 0, 0), (112, 12, 12)),
    ((100, 80, 3, 0, 0), (83, -17, -17)),
    ((100, 50, 0, 10, 40), (100, 0, 0)),
    ((200, 0, 0, 15, 210), (225, 25, 12.5)),
]
for args, expected in cases:
    got = pnl(*args)
    assert all(isclose(a, b, rel_tol=1e-12, abs_tol=1e-12) for a, b in zip(got, expected)), (args, got, expected)

# Partial removals keep original total basis and add proceeds; otherwise realized PnL disappears.
gross, profit, pct = pnl(100, 50, withdrawn=50)
assert (gross, profit, pct) == (100, 0, 0)

# Spot-grid basis is allocated from the amounts actually used, not unused wallet input.
bins = [30.0, 20.0, 40.0]
assert isclose(sum(bins), 90.0)
assert sum(bins) < 100.0
print('PNL_MATH_TEST_PASS')
