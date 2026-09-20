#!/usr/bin/env python3
from pathlib import Path

src = Path(__file__).with_name('index.html').read_text(encoding='utf-8')

# No manual accounting controls, prompts, or helper remain.
for forbidden in [
    'data-act="basis"',
    '>Set basis<',
    'window.prompt(',
    'function setPnlBaseline(',
    "'manual-baseline'",
    'Basis · Share',
    'Cost basis unavailable',
]:
    assert forbidden not in src, f'manual basis UI/code remains: {forbidden}'

# Accounting remains automatic for every transaction path managed by UNISARC.
assert src.count('recordPnlDeposit(') >= 4, 'automatic mint/increase/grid basis tracking missing'
assert 'recordPnlClaim(tokenId' in src, 'automatic claim tracking missing'
assert 'reducePnlCost(tokenId, pct' in src, 'automatic removal tracking missing'
assert "pnlStatus = 'unavailable'" in src, 'legacy positions must remain safely untracked'
assert "const pnlText = hasPnl ?" in src and ": '—';" in src, 'legacy PnL must render as a simple dash'
assert '<div class="k">Share</div>' in src, 'share must remain visible without basis UI'

print('AUTOMATIC_BASIS_UI_TEST_PASS')
