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

    # Token metadata (all pool types) so the frontend can list V4 pools that
    # RadarDex does not index. Quote-colliding symbols (USDC rows that are
    # actually memecoins) keep their token NAME as displaySymbol.
    tokens_list = []
    for t in toks:
        sym = str(t.get('symbol') or '?')
        display = sym
        if sym.upper() == 'USDC' and t.get('name'):
            display = str(t['name'])
        try:
            liq = float(t.get('liquidity_usd') or 0)
        except (TypeError, ValueError):
            liq = 0.0
        try:
            vol = float(t.get('volume_24h') or 0)
        except (TypeError, ValueError):
            vol = 0.0
        tokens_list.append({
            'address': str(t.get('address') or '').lower(),
            'symbol': sym,
            'displaySymbol': display,
            'name': str(t.get('name') or sym),
            'decimals': t.get('decimals'),
            'liquidity_usd': liq,
            'volume_24h': vol,
            'price_usd': t.get('price_usd') or 0,
            'icon': t.get('icon_url') or '',
            'pool_type': t.get('pool_type') or '',
            'pool_address': t.get('pool_address') or '',
            'pool_hooks': t.get('pool_hooks') or '',
            'pool_real_fee': t.get('pool_real_fee') or '',
            'quote_address': t.get('quote_address') or '',
            'quote_symbol': t.get('quote_symbol') or '',
            'market_cap_usd': t.get('market_cap_usd') or 0,
            'change_24h': t.get('price_change_24h') or 0,
            'txns_24h': t.get('txns_24h') or 0,
            'buys_24h': t.get('buys_24h') or 0,
            'sells_24h': t.get('sells_24h') or 0,
            'sparkline': t.get('sparkline_data') or [],
        })

    return {'tokens': len(toks), 'tokens_list': tokens_list, 'swaps': swaps}


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
        n = max(1, min(n, 50))
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
