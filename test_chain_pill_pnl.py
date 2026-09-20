#!/usr/bin/env python3
from pathlib import Path

src = Path(__file__).with_name('index.html').read_text(encoding='utf-8')

# 1. The "ARC Mainnet" chain pill must be gone from the header.
assert 'class="chain-pill"' not in src, 'chain pill markup still present'
assert 'id="chainName"' not in src, 'chain pill label still present'
assert '.chain-pill{' not in src, 'chain pill CSS still present'

# 2. PnL must backfill a cost basis for existing positions instead of showing "—".
assert 'function backfillPnlLedger' in src, 'PnL backfill helper missing'
assert 'applyBackfilledPnl' in src, 'PnL backfill apply step missing'
assert 'raw.forEach(applyBackfilledPnl)' in src, 'PnL backfill not invoked on positions'
assert 'legacy' in src.lower(), 'legacy-position cost-basis bootstrap missing'
print('CHAIN_PILL_PNL_TEST_PASS')
