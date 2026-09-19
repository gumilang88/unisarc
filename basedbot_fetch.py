#!/usr/bin/env python3
"""BasedBot fetch helper — bypasses Cloudflare TLS fingerprinting via curl_cffi.

Modes:
  1) single path:  python3 basedbot_fetch.py "/api/tokens?chain=5042&limit=50"
       -> prints upstream JSON for that path
  2) batch feed:   python3 basedbot_fetch.py --feed <ntokens> <perToken>
       -> fetches the top tokens by 24h volume, then each token's recent trades
          in parallel (one warm session), prints a merged JSON:
          { "tokens": [...], "swaps": [ {symbol,address,is_buy,volume_usd,price_usd,tx_hash,trader,timestamp}, ... ] }

stdout is always JSON; server.js proxies it verbatim.
"""
import sys
import json
from concurrent.futures import ThreadPoolExecutor
from curl_cffi import requests as cr

BASE = 'https://basedbot.app'


def get(sess, path, timeout=20):
    r = sess.get(BASE + path, timeout=timeout)
    r.raise_for_status()
    return r.json()


def feed_mode(ntokens, per_token):
    sess = cr.Session(impersonate='chrome')
    j = get(sess, '/api/tokens?chain=5042&limit=100&timeframe=24h&tab=top')
    toks = (j.get('data') or [])[:ntokens]

    def trades(t):
        addr = str(t.get('address') or '')
        pool = t.get('pool_address')
        if not addr or not pool:
            return []
        try:
            tj = get(sess, f'/api/token/{addr}/trades?chain=5042&pool={pool}&sort=desc')
            return tj.get('data') or []
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=min(ntokens, 12)) as ex:
        per_tok_trades = list(ex.map(trades, toks))

    swaps = []
    for t, trs in zip(toks, per_tok_trades):
        sym = t.get('symbol') or '?'
        # 'USDC' symbols are quote rows on basedbot — use the token name for clarity
        if str(sym).upper() == 'USDC' and t.get('name'):
            sym = t['name']
        for tr in trs[:per_token]:
            vol = tr.get('volume_usd')
            try:
                vol = float(vol)
            except (TypeError, ValueError):
                continue
            if not vol or vol <= 0:
                continue
            swaps.append({
                'symbol': sym,
                'token': str(t.get('address') or '').lower(),
                'is_buy': bool(tr.get('is_buy')),
                'volume_usd': vol,
                'price_usd': tr.get('price_usd'),
                'tx_hash': tr.get('tx_hash') or '',
                'trader': tr.get('trader_full') or tr.get('trader') or '',
                'timestamp': tr.get('timestamp') or '',
                'pool_type': t.get('pool_type') or '',
            })

    # newest first (timestamp format: "2026-09-19 19:49:03", UTC)
    swaps.sort(key=lambda s: s['timestamp'] or '', reverse=True)
    return {'tokens': len(toks), 'swaps': swaps}


def main():
    args = sys.argv[1:]
    if not args:
        print(json.dumps({'error': 'missing args'}))
        sys.exit(1)

    if args[0] == '--feed':
        try:
            n = int(args[1]) if len(args) > 1 else 12
            per = int(args[2]) if len(args) > 2 else 30
        except ValueError:
            n, per = 12, 30
        n = max(1, min(n, 30))
        per = max(1, min(per, 100))
        try:
            out = feed_mode(n, per)
        except Exception as e:
            print(json.dumps({'error': str(e)[:200]}))
            sys.exit(1)
        sys.stdout.write(json.dumps(out))
        return

    raw = args[0]
    # Only allow GET on basedbot.app API paths — no other hosts, no scheme tricks.
    if not raw.startswith('/api/'):
        print(json.dumps({'error': 'path must start with /api/'}))
        sys.exit(1)
    if '\r' in raw or '\n' in raw or ' ' in raw:
        print(json.dumps({'error': 'bad path'}))
        sys.exit(1)
    try:
        sess = cr.Session(impersonate='chrome')
        sys.stdout.write(json.dumps(get(sess, raw)))
    except Exception as e:
        print(json.dumps({'error': str(e)[:200]}))
        sys.exit(1)


if __name__ == '__main__':
    main()
