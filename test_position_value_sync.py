#!/usr/bin/env python3
from pathlib import Path
import re

src = Path(__file__).with_name('index.html').read_text(encoding='utf-8')

# Position valuation must use the actual token amounts represented by this NFT,
# normalized by each token's own decimals. Pool-liquidity share × TVL is invalid
# for concentrated V3 ranges and caused a ~$1 deposit to display around $9.
assert 'function positionTokenAmounts(' in src, 'missing exact V3 position amount helper'
assert re.search(r"pos\.value\s*=\s*amount0\s*\*\s*dollarPer0\s*\+\s*amount1\s*\*\s*dollarPer1", src), 'position value must be token amount × synchronized USD price'
assert not re.search(r"pos\.value\s*=\s*share\s*\*\s*poolInfo\.tvl", src), 'invalid V3 share × TVL valuation remains'
assert re.search(r"amount0\s*=.*\/\s*\(10\s*\*\*\s*m0\.decimals\)", src), 'token0 decimals normalization missing'
assert re.search(r"amount1\s*=.*\/\s*\(10\s*\*\*\s*m1\.decimals\)", src), 'token1 decimals normalization missing'

# Every Radar token is keyed by address, so symbol collisions/case differences do
# not desynchronize price, icon, metadata, and a wallet position.
assert 'radarTokenByAddress' in src, 'missing address-indexed Radar token registry'
assert 'radarTokens: {}' in src, 'full Radar registry missing from state'
assert "limit=500&window=24h" in src, 'position pricing must load the full 500-token market registry'
assert re.search(r"S\.radarTokens\[tokenAddr\]\s*=", src), 'Radar registry must be populated before the UI TVL filter'
assert re.search(r"const live = await fetchRadarTop\(\);[\s\S]{0,700}if \(S\.address\) await loadPositionsUI\(\);", src), 'wallet positions must wait for full market synchronization'
assert re.search(r"setInterval\(async \(\) =>[\s\S]{0,500}syncTokenMetaFromPools\(\);[\s\S]{0,300}await loadPositionsUI\(\);", src), '60-second price refresh must also refresh position values'
assert 'syncTokenMetaFromPools' in src, 'missing token metadata synchronization'
assert re.search(r"poolInfo\s*=\s*radarTokenByAddress\(", src), 'position enrichment must resolve market data by token address'
assert 'priceSource' in src, 'position must expose valuation source for diagnostics'
assert "slotRaw.slice(104, 128)" in src, 'slot0 tick must be decoded from the signed int24 tail of word 2'

print('POSITION_VALUE_SYNC_TEST_PASS')
