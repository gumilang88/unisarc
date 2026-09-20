#!/usr/bin/env python3
from pathlib import Path
src=Path(__file__).with_name('index.html').read_text(encoding='utf-8')
assert "if (v==='monitor')" in src, 'monitor navigation hook missing'
assert 'ensureMonitorPools' in src, 'monitor data loader missing'
assert "S.pools = poolsFromSnapshot()" in src, 'snapshot fallback missing'
assert 'renderMonitor();' in src, 'monitor render call missing'
assert '_monitorLoadPromise' in src, 'duplicate monitor fetch guard missing'
print('MONITOR_NAV_TEST_PASS')
