#!/usr/bin/env python3
from pathlib import Path
import re

src = Path(__file__).with_name('index.html').read_text(encoding='utf-8')

assert 'id="binTabBins">Spot Grid' in src, 'BINS Grid button must be renamed Spot Grid'
assert 'Spot Grid splits capital across consecutive V3 ranges' in src, 'Spot Grid description missing'
assert re.search(r"function\s+spotBinSide\s*\(", src), 'spotBinSide helper missing'
assert re.search(r"function\s+spotWeights\s*\(", src), 'spotWeights helper missing'
assert "const side = spotBinSide(sg.tl, sg.tu, curTick)" in src, 'plan must classify each bin by current tick'
assert "const activeCount = binPlan.filter(x => x.side === 'active').length" in src, 'summary must count active bins'
assert "const bidCount = binPlan.filter(x => x.side === 'bid').length" in src, 'summary must count bid bins'
assert "const askCount = binPlan.filter(x => x.side === 'ask').length" in src, 'summary must count ask bins'
assert "if (side === 'bid')" in src and "else if (side === 'ask')" in src, 'one-sided allocation branches missing'
assert "if (side === 'bid') amt0 = 0n" in src and "else if (side === 'ask') amt1 = 0n" in src, 'Spot Grid must zero the unavailable side'
assert "BID · USDC only" in src and "ASK · Token only" in src, 'visual Spot Grid zone labels missing'
assert "50/50 ke tiap sisi" not in src, 'old per-bin 50/50 logic still present'
print('SPOT_GRID_TEST_PASS')
