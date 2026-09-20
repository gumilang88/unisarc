#!/usr/bin/env python3
from pathlib import Path
import re

src = Path(__file__).with_name('index.html').read_text(encoding='utf-8')
required = [
    "function tickPriceTokenUsd(",
    "function spotRangeAmounts(",
    "function fitSpotPlanToDeposits(",
    "function validateSpotPlan(",
    "poolToken0",
    "poolToken1",
    "requiredA",
    "requiredB",
    "availableA",
    "availableB",
    "unusedA",
    "unusedB",
    "Effective deposit",
]
for needle in required:
    assert needle in src, f'missing synchronized Spot Grid logic: {needle}'
assert "Math.round(usd0 / px * 10 ** decA)" not in src, 'old approximate amount formula still present'
assert "Math.round(usd1 * 10 ** decB)" not in src, 'old approximate amount formula still present'
assert "const spotRequiredA = binMode ? binPlan.reduce" in src, 'allowance must use summed Spot Grid requirement A'
assert "const spotRequiredB = binMode ? binPlan.reduce" in src, 'allowance must use summed Spot Grid requirement B'
assert "validateSpotPlan(binPlan" in src, 'pre-send validation missing'
# BID/ASK planning must preserve both one-sided ranges; dropping a leg causes
# an invalid allowance/mint plan and on-chain mint reverts.
assert "fitSpotPlanToDeposits(provisional, availableA, availableB, false)" in src, 'BID/ASK plan must not discard one-sided ranges'
assert "fitSpotPlanToDeposits(provisional, availableA, availableB, true)" not in src, 'legacy partial-fit drops BID/ASK ranges'
# LP approval must cover the freshly rebuilt plan and be confirmed by a
# post-transaction on-chain allowance read before mint proceeds.
assert "const maxUint256 = (1n << 256n) - 1n;" in src, 'LP approval buffer missing'
assert "approval confirmed but allowance is still below LP amount" in src, 'post-approval allowance guard missing'
# BID/ASK mint must use zero amount minimums so a live price change does not
# reject an otherwise valid one-sided range.
assert "bin.tl, bin.tu, a0wei, a1wei, S.address, deadline, 0n, 0n" in src, 'BID/ASK mint still has slippage minimums'
# A freshly minted one-sided grid is staged around current price, not failed.
assert "label: 'BID STAGED'" in src, 'BID staged status missing'
assert "label: 'ASK STAGED'" in src, 'ASK staged status missing'
assert "label: 'BID OUT RANGE'" not in src, 'BID incorrectly flagged out of range'
assert "label: 'ASK OUT RANGE'" not in src, 'ASK incorrectly flagged out of range'
# Arc NFPM rejects nested mint callbacks in multicall. BID and ASK must be
# sent as individually confirmed zero-min mints so callback accounting stays valid.
assert "for (const bin of executionPlan)" in src, 'BID/ASK sequential execution missing'
assert "sendTx(CFG.nfpm, data)" in src, 'BID/ASK direct NFPM mint missing'
assert "BID + ASK in one transaction" not in src, 'unsupported nested mint multicall still active'
assert "if (ids.length !== 1)" in src, 'each direct mint must resolve exactly one token ID'
# Multicall encoder remains valid for remove-liquidity flows.
assert "let offset = (calls.length + 1) * 32;" in src, 'NFPM multicall bytes[] offsets are malformed'
print('SPOT_GRID_MATH_TEST_PASS')
