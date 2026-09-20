#!/usr/bin/env python3
from pathlib import Path

src = Path(__file__).with_name('index.html').read_text(encoding='utf-8')

# fetchHeatTokens must merge BasedBot V4 tokens (dedup by address, UNISWAP_V4 only)
assert "Merge BasedBot V4 tokens so the heatmap picker" in src, 'heat tokens V4 merge missing'
assert "if (String(t.pool_type || '').toUpperCase() !== 'UNISWAP_V4') continue;" in src, 'V4-only filter missing in heat merge'
heat = src[src.index('async function fetchHeatTokens'):]
heat = heat[:heat.index('function openHeatOverlay')]
assert heat.count('versions: [\'v4\']') == 1, 'heat merge must tag versions v4'

# _momToks (pool quality scanner) merge already existed — confirm still present
assert "Merge BasedBot V4 tokens (RadarDex does not index Uniswap V4 pools at all)." in src

# V4 badge rendered on tools cards
assert '.ho-v4{' in src, 'V4 badge CSS missing'
assert 'ho-v4">V4' in src, 'V4 badge not rendered anywhere'
for anchor, label in [
    ('spot-sym">${best.symbol}', 'spotlight'),
    ('ld-top"><span>${it.sym}', 'liquidity distribution'),
    ('mig-sym">${x.t.symbol}', 'migration tracker'),
    ('poolq-pair-name">USDC / ${sym}', 'pool quality scanner'),
    ('ho-sym">${sym}', 'heat picker'),
]:
    i = src.index(anchor)
    window = src[i:i+400]
    assert 'ho-v4' in window, f'V4 badge missing on {label}'

# realtime loop re-renders the heat-driven cards
loop = src[src.index('_toolsNet = setInterval'):]
loop = loop[:loop.index('}, 8000);')]
for fn in ['renderGainersLosers', 'renderSpotlight', 'renderLiquidityDistribution']:
    assert fn in loop, f'{fn} not in realtime loop'
print('TOOLS_V4_MERGE_TEST_PASS')
