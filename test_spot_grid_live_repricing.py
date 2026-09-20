#!/usr/bin/env python3
from pathlib import Path

src = Path(__file__).with_name('index.html').read_text(encoding='utf-8')

assert 'const SPOT_LIVE_POLL_MS = 1000;' in src, '1-second live Spot Grid polling missing'
assert 'function startSpotLivePricing()' in src and 'function stopSpotLivePricing()' in src, 'live pricing lifecycle missing'
assert "setInterval(() => { if (binMode && $('modalAdd').classList.contains('open')) planBins({ forceLive: true }); }, SPOT_LIVE_POLL_MS)" in src, 'modal must refresh Spot Grid from chain while open'
assert 'async function getSpotPoolContext(tokenA, tokenB, feeHint=0, poolHint=null, forceLive=false)' in src, 'Spot context needs force-live mode'
assert 'const freshSlot = forceLive ? await poolSlot0(cachedValue.poolAddr)' in src, 'cached metadata must refresh slot0 instead of caching price'
assert 'async function planBins(options={})' in src and 'const forceLive = !!options.forceLive;' in src, 'planner must support forced live repricing'
assert 'await planBins({ forceLive: true });' in src, 'mint must rebuild the plan just in time'
assert 'const executionPlan = binPlan.map(x => ({ ...x }));' in src, 'mint must freeze the freshly rebuilt plan'
assert 'spotCtx.slot.tick !== plannedTick' in src and "await planBins({ forceLive: true });" in src, 'mint must rebuild again if tick moves during preparation'
assert 'for (const bin of executionPlan)' in src, 'mint loop must use the fresh execution plan'
assert 'stopSpotLivePricing();' in src, 'live poll must stop when modal/mode closes'
print('SPOT_GRID_LIVE_REPRICING_TEST_PASS')
