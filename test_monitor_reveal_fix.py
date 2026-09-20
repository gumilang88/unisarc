#!/usr/bin/env python3
from pathlib import Path
import re

src = Path(__file__).with_name('index.html').read_text(encoding='utf-8')

# Anchor on the reveal selector that contains '.home-hero' specifically.
m = re.search(r"const sel = '\.home-hero.*?';", src, re.S)
assert m, 'reveal selector with .home-hero not found'
sel = m.group(0)

# Data lists must NOT get scroll-reveal (leaves below-fold cards stuck at opacity:0, esp mobile).
for forbidden in ['.mon-card', '.mon-grid', '.pos-card', '.pos-grid', '.rw-row', '.reward-hero', '.stat']:
    assert forbidden not in sel, f'{forbidden} still in reveal selector'

# Home/marketing blocks keep reveal.
assert '.home-hero' in sel, 'home reveal blocks lost'
assert '.px-card' in sel, 'px-card reveal lost'
print('MONITOR_REVEAL_FIX_TEST_PASS')
