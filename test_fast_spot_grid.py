#!/usr/bin/env python3
from pathlib import Path

src = Path(__file__).with_name('index.html').read_text(encoding='utf-8')

assert "'https://arc-mainnet.infura.io/v3/b6bf7d3508c941499b10025c0776eaf8',\n    'https://rpc.arc-scan.org'" in src, 'fast RPC must be first'
assert 'const RPC_TIMEOUT_MS = 3500;' in src, 'RPC timeout missing'
assert 'Promise.any(CFG.rpcUrls.map' in src, 'RPC reads must race endpoints instead of waiting serially'
assert 'const SPOT_PLAN_CACHE_MS = 12000;' in src, 'Spot Grid cache TTL missing'
assert 'function schedulePlanBins()' in src, 'debounced Spot Grid scheduler missing'
assert "addEventListener('input', schedulePlanBins)" in src, 'Spot Grid inputs must use debounced scheduler'
assert 'const cached = spotPoolCache.get(cacheKey);' in src, 'Spot Grid pool metadata cache missing'
assert 'const [t0Hex, t1Hex, feeHex] = await Promise.all([' in src, 'pool metadata reads must run concurrently'
assert 'const TX_POLL_MS = 500;' in src, 'fast transaction receipt polling missing'
assert "window.ethereum.request\n        ? window.ethereum.request({ method: 'eth_getTransactionReceipt'" in src, 'receipt polling must query wallet RPC first'
assert 'const preflight = rpc(' in src and 'await Promise.race([preflight' in src, 'transaction simulation must have a fast bounded preflight'
assert 'getSpotPoolContext(tokAAddr, tokBAddr, p.fee || 0, p, true)' in src, 'execution must reuse cached metadata with a fresh live slot0'
print('FAST_SPOT_GRID_TEST_PASS')
