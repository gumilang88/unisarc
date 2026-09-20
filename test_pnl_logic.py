#!/usr/bin/env python3
from pathlib import Path
import re

src = Path(__file__).with_name('index.html').read_text(encoding='utf-8')

required = [
    'function pnlStorageKey(',
    'function readPnlLedger(',
    'function writePnlLedger(',
    'function pnlSnapshot(',
    'function applyPnlToPosition(',
    'function recordPnlDeposit(',

    'function reducePnlCost(',
    'function extractNfpmTokenIds(',
    'function txReceipt(',
    'pnlStatus',
    'pnlPct',
    'costBasisUsd',
    'PnL',
]
for needle in required:
    assert needle in src, f'missing PnL component: {needle}'

# Exact total-return model: current principal + unclaimed fees + claimed/withdrawn value - net contributed capital.
assert re.search(r"grossValue\s*=\s*currentValue\s*\+\s*claimableFees\s*\+\s*claimedValue\s*\+\s*withdrawnValue", src), 'gross PnL value formula missing'
assert re.search(r"profitUsd\s*=\s*grossValue\s*-\s*contributedUsd", src), 'profit-minus formula missing'
assert re.search(r"profitPct\s*=\s*contributedUsd\s*>\s*0\s*\?\s*profitUsd\s*/\s*contributedUsd\s*\*\s*100", src), 'profit percent formula missing'

# New positions and Add-to-existing must both record basis; BINS must distribute it per minted NFT.
assert src.count('recordPnlDeposit(') >= 4, 'not every Add-LP path records cost basis'
assert 'extractNfpmTokenIds(receipt' in src, 'minted NFT tokenId must come from transaction receipt'
assert 'reducePnlCost(tokenId, pct' in src, 'remove path must record withdrawn value'
assert 'recordPnlClaim(tokenId' in src, 'claim path must track claimed fee value'

# Legacy positions cannot be shown as fake profit; they must be explicitly unavailable.
assert "pos.pnlStatus = 'unavailable'" in src, 'legacy/unknown basis must be unavailable'
assert 'Cost basis unavailable' not in src, 'legacy PnL must not expose manual accounting language'
assert 'data-act="basis"' not in src, 'manual basis input must not exist'
assert 'function setPnlBaseline(' not in src, 'manual basis helper must not exist'
assert 'Estimated profit' not in src, 'must not invent estimated profit'
print('PNL_LOGIC_TEST_PASS')
