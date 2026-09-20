#!/usr/bin/env python3
from pathlib import Path

src = Path(__file__).with_name('index.html').read_text(encoding='utf-8')

assert '.all-position-grid{' in src, 'shared position grid missing'
assert 'grid-template-columns:repeat(auto-fill,240px)' in src, 'desktop cards must stay compact instead of stretching across the row'
assert 'class="all-position-grid"' in src, 'shared container must use the compact grid'
assert '.positions-box .pos-card{' in src, 'shared-container compact card styling missing'
assert '.positions-box .pos-actions .px-btn{' in src, 'position actions must remain compact'
assert '@media(max-width:620px)' in src and '.all-position-grid{grid-template-columns:minmax(0,1fr)}' in src, 'mobile must use one fluid column'
print('POSITION_CARDS_GRID_TEST_PASS')
