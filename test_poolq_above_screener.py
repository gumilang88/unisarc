#!/usr/bin/env python3
from pathlib import Path

src = Path(__file__).with_name('index.html').read_text(encoding='utf-8')

poolq = src.index('id="poolqGrid"')
scr = src.index('id="scrBody"')
assert poolq < scr, 'LP Pool Quality Scanner must appear above Pairs Screener'
print('TOOLS_POOLQ_ABOVE_SCREENER_TEST_PASS')
