#!/usr/bin/env python3
from pathlib import Path
src=Path(__file__).with_name('index.html').read_text(encoding='utf-8')
checks={
 'grid equal rows':'grid-auto-rows:1fr' in src,
 'card full height':'height:100%' in src and '.mon-card' in src,
 'card fixed regions':'grid-template-rows:auto auto auto 64px auto auto' in src,
 'header no wrap':'.mon-top' in src and 'flex-wrap:nowrap' in src,
 'token name ellipsis':'.mon-top .nm' in src and 'text-overflow:ellipsis' in src,
 'price constrained':'.mon-top .pr' in src and 'white-space:nowrap' in src,
 'footer pinned':'.mon-actions' in src and 'margin-top:auto' in src,
 'inline action removed':'class="mon-actions"' in src,
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL')+': '+k)
assert all(checks.values())
print('MONITOR_CARD_LAYOUT_TEST_PASS')
