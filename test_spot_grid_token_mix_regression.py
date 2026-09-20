#!/usr/bin/env python3
from pathlib import Path

src = Path(__file__).with_name('index.html').read_text(encoding='utf-8')

assert "function fitSpotPlanToDeposits(plan, availableA, availableB, allowPartial=false)" in src, \
    'Spot Grid fitter must support partial, one-sided budgets without changing entered amounts'
assert "const fit = fitSpotPlanToDeposits(provisional, availableA, availableB, true);" in src, \
    'Spot Grid planner must retain fundable bins when one side is insufficient'
assert "binPlan.length < 1" in src, \
    'A valid one-sided Spot Grid must not require at least two funded positions'
assert "Cannot fund any position with the entered token amounts" in src, \
    'True zero-fundable plans need a precise error instead of insufficient token mix'
assert "Insufficient token mix" not in src, \
    'The misleading insufficient-token-mix blocker must be removed'
print('SPOT_GRID_TOKEN_MIX_REGRESSION_PASS')
