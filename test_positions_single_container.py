#!/usr/bin/env python3
from pathlib import Path

src = Path(__file__).with_name('index.html').read_text(encoding='utf-8')

assert 'class="positions-box"' in src, 'all positions need one shared outer box'
assert 'class="all-position-grid"' in src, 'positions need one shared compact grid'
assert "list.map(positionCardHtml).join('')" in src, 'all filtered positions must render directly into the shared grid'
for marker in ['class="pg-head"', 'class="pg-stat"', 'data-group-toggle', 'Individual Positions']:
    assert marker not in src, f'old grouped summary UI remains: {marker}'
assert "$('positionGroups').addEventListener('click', e=>{" in src, 'position action delegation must remain active'
assert "const btn = e.target.closest('button[data-act]');" in src, 'Add/Remove/Claim actions must remain wired'
print('POSITIONS_SINGLE_CONTAINER_TEST_PASS')
