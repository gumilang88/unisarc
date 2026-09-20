#!/usr/bin/env python3
from pathlib import Path
import re

src = Path(__file__).with_name('index.html').read_text(encoding='utf-8')

# Rewards is embedded below positions and removed as a separate route/nav item.
assert 'id="positionsRewards"' in src, 'embedded rewards section missing from positions'
assert src.index('id="posGrid"') < src.index('id="positionsRewards"'), 'rewards must sit below positions'
assert 'data-v="rewards"' not in src, 'separate Rewards nav remains'
assert 'id="view-rewards"' not in src, 'separate Rewards view remains'
assert "['home','positions','add','monitor','tools']" in src, 'routing still exposes rewards'

# Portfolio chart is completely removed from Positions.
for marker in ['id="portfolioChart"', 'id="tfTabs"', 'id="chartPeriod"']:
    assert marker not in src, f'portfolio value UI remains: {marker}'
assert 'drawPortfolioChart();' not in src, 'portfolio chart is still rendered'

# Every position now lives in one shared container; pair-level summary strips are gone.
for marker in ['function renderPositionGroups(', 'id="positionGroups"', 'class="positions-box"', 'class="all-position-grid"']:
    assert marker in src, f'single positions container missing: {marker}'
for marker in ['class="pg-head"', 'class="pg-stat"', 'data-group-toggle', 'Individual Positions']:
    assert marker not in src, f'legacy grouped summary remains: {marker}'

print('POSITIONS_GROUPING_LAYOUT_TEST_PASS')
