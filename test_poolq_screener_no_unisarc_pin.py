#!/usr/bin/env python3
from pathlib import Path

src = Path(__file__).with_name('index.html').read_text(encoding='utf-8')

# Pool Quality scanner must NOT force UNISARC to #1.
assert "if ((a.t.symbol || '').toUpperCase() === 'UNISARC') return -1;" not in src, 'pool quality still pins UNISARC first'
assert "if ((b.t.symbol || '').toUpperCase() === 'UNISARC') return 1;" not in src, 'pool quality still pins UNISARC first'

# Pair screener must NOT remove-and-prepend UNISARC; it must flow through the same sort.
assert "let pinned = [];" not in src, 'screener still uses a pinned-UNISARC prepend'
assert "pinned = [_uniTok];" not in src, 'screener still prepends UNISARC token'
assert "rows = pinned.concat(toks)" not in src, 'screener still concatenates pinned UNISARC ahead of sorted rows'

# The shared scanner list must still merge the low-volume UNISARC token (so it appears),
# but by ordinary sort order, not force-first.
assert "poolQualityRows" in src and "renderSmBody" in src, 'scanner/screener renderers missing'
print('POOLQ_SCREENER_NO_UNISARC_PIN_TEST_PASS')
