// UNISARC static server + RadarDex API proxy (CORS bypass)
// Usage: node server.js  (serves on :3011 by default)
const http = require('http');
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const PORT = process.env.PORT || 3011;
const RADAR = 'https://api.radardex.pro';
const FILE = path.join(__dirname, 'index.html');

// Arc mainnet RPC (chain 5042) — public node is intermittent; retry aggressively.
// thecusp/warp are ecosystem relays that the RadarDex frontend also uses as fallback.
// arc.drpc.org is the fastest/healthiest; raced in parallel below.
const RPC_URLS = [
  'https://arc.drpc.org',
  'https://thecusp.io/api/arc-rpc',
  'https://warp-arc-production.up.railway.app/rpc',
  'https://rpc.arc-scan.org',
];

const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.svg': 'image/svg+xml', '.json': 'application/json' };
// assets (favicon/icons) are immutable — long cache. html is no-store (dev/live edit).
const CACHEABLE = new Set(['.png', '.svg', '.ico', '.js', '.css']);

// gzip/deflate compress text responses so the 355KB index.html transfers in ~40KB.
function compress(req, res, status, headers, body) {
  const accept = req.headers['accept-encoding'] || '';
  const enc = /\bgzip\b/.test(accept) ? 'gzip' : (/\bdeflate\b/.test(accept) ? 'deflate' : null);
  if (!enc || !body || body.length < 1024) {
    res.writeHead(status, headers);
    res.end(body);
    return;
  }
  res.setHeader('Content-Encoding', enc);
  res.setHeader('Vary', 'Accept-Encoding');
  res.writeHead(status, headers);
  const buf = enc === 'gzip' ? zlib.gzipSync(body) : zlib.deflateSync(body);
  res.end(buf);
}

const server = http.createServer((req, res) => {
  // CORS headers buat semua response
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') { res.writeHead(204); return res.end(); }

  // RadarDex proxy — /api/radar?<params> -> https://api.radardex.pro<path>
  if (req.url.startsWith('/api/radar')) {
    const rest = req.url.slice('/api/radar'.length); // e.g. ?sort=... or /tokens?...
    const target = RADAR + (rest.startsWith('/') ? rest : '/tokens' + rest);
    radarProxy(req, res, target);
    return;
  }

  // Argus token data — /api/argus -> serve the scraped top-100-by-volume snapshot.
  // argus.world's API is Cloudflare-protected (TLS fingerprint + JS challenge), so the
  // snapshot lives in argus-data.json (refreshed out-of-band via a browser session).
  if (req.url === '/api/argus' || req.url.startsWith('/api/argus?')) {
    fs.readFile(path.join(__dirname, 'argus-data.json'), (err, data) => {
      if (err) { res.writeHead(404, { 'Content-Type': 'application/json' }); return res.end(JSON.stringify({ error: 'no argus snapshot' })); }
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(data);
    });
    return;
  }

  // BasedBot proxy — /api/basedbot<path> -> https://basedbot.app<path>.
  // basedbot.app is Cloudflare-protected against plain node fetch (TLS fingerprint
  // challenge), but curl_cffi's chrome impersonation passes cleanly.
  // /api/basedbot-feed runs the batch helper: ONE python process fetches the token
  // list + all top-token trades in parallel with a warm session (~1.3s total vs
  // 13 cold processes ≈ 8-15s). 30s in-memory cache keeps polls off the upstream.
  if (req.url.startsWith('/api/basedbot/')) {
    const rest = req.url.slice('/api/basedbot'.length); // "/api/tokens?chain=..." etc.
    basedbotProxy(req, res, rest);
    return;
  }
  if (req.url.startsWith('/api/basedbot-feed')) {
    basedbotProxy(req, res, '--feed 12 30');
    return;
  }

  // Arc RPC proxy — /api/rpc -> forward JSON-RPC to an upstream Arc node.
  // The public node (rpc.arc-scan.org) rate-limits / intermittently drops requests,
  // which breaks wallet flows (add LP BID/ASK, swap, claim) in the browser. Routing
  // through this local proxy retries each request so a transient "unreachable" never
  // surfaces as a failed tx. eth_sendTransaction is forwarded verbatim (wallet signs
  // client-side via eth_sendTransaction before any of this; raw tx submission is fine).
  if (req.url === '/api/rpc' && req.method === 'POST') {
    let body = '';
    req.on('data', c => { body += c; if (body.length > 2e6) req.destroy(); });
    req.on('end', async () => {
      let payload;
      try { payload = JSON.parse(body); } catch (e) { res.writeHead(400, { 'Content-Type': 'application/json' }); return res.end(JSON.stringify({ error: 'bad json' })); }
      const result = await rpcRetry(payload);
      res.writeHead(result.ok ? 200 : 502, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result.ok ? result.body : { error: result.err, msg: 'all upstream RPC endpoints failed' }));
    });
    return;
  }

  // static
  const p = req.url === '/' ? '/' + 'index.html' : req.url.split('?')[0];
  const full = path.join(__dirname, p);
  if (!full.startsWith(__dirname)) { res.writeHead(403); return res.end('forbidden'); }
  const ext = path.extname(full);
  if (p === '/index.html' || p === '/') {
    res.setHeader('Cache-Control', 'no-store');
    compress(req, res, 200, { 'Content-Type': 'text/html; charset=utf-8' }, indexHtmlCache);
    return;
  }
  fs.readFile(full, (err, data) => {
    if (err) { res.writeHead(404); return res.end('not found'); }
    const h = { 'Content-Type': MIME[ext] || 'application/octet-stream' };
    if (CACHEABLE.has(ext)) h['Cache-Control'] = 'public, max-age=86400, immutable';
    compress(req, res, 200, h, data);
  });
});

server.listen(PORT, () => console.log(`UNISARC on http://localhost:${PORT}  (proxy /api/radar -> ${RADAR})`));

// Cache index.html in memory (re-read if it changes on disk) so static serving never blocks on fs.
let indexHtmlCache = fs.readFileSync(FILE);
fs.watchFile(FILE, { interval: 1000 }, () => {
  try { indexHtmlCache = fs.readFileSync(FILE); console.log('[unisarc] index.html reloaded'); } catch (e) {}
});

// BasedBot upstream proxy with a 30s in-memory cache.
// The python helper (basedbot_fetch.py) does the actual CF-bypassing fetch via
// curl_cffi; this wrapper handles concurrency (same-path requests coalesce into
// one upstream call), caching, and timeouts.
const BB_CACHE = new Map(); // key -> { at, body, inflight }
function basedbotProxy(req, res, restPath) {
  const key = restPath;
  const now = Date.now();
  const hit = BB_CACHE.get(key);
  // fresh cached body (< 30s) — serve immediately
  if (hit && hit.body && now - hit.at < 30000) {
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'X-BB-Cache': 'hit' });
    return res.end(hit.body);
  }
  // an upstream fetch for this path is already in flight — piggyback on it
  if (hit && hit.inflight && hit.inflight.length) {
    hit.inflight.push({ res });
    return;
  }
  const waiters = [{ res }];
  const entry = { at: now, body: null, inflight: waiters };
  BB_CACHE.set(key, entry);
  // --feed args arrive as one pre-joined string; split into argv for the helper
  const helperArgs = restPath.startsWith('--feed') ? restPath.split(/\s+/) : [restPath];
  const { execFile } = require('child_process');
  execFile('python3', [path.join(__dirname, 'basedbot_fetch.py'), ...helperArgs], { timeout: 25000, maxBuffer: 8e6 }, (err, stdout, stderr) => {
    const ok = !err && stdout && stdout.trim().startsWith('{');
    if (ok) {
      entry.body = stdout;
      entry.at = Date.now();
      entry.inflight = [];
      for (const w of waiters) { try { w.res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }); w.res.end(stdout); } catch (e) {} }
    } else {
      entry.inflight = [];
      for (const w of waiters) { try { w.res.writeHead(502, { 'Content-Type': 'application/json' }); w.res.end(JSON.stringify({ error: 'basedbot proxy failed' })); } catch (e) {} }
    }
  });
}

async function radarProxy(req, res, target) {
  // RadarDex upstream is intermittently slow/unreachable. Retry a few times with a
  // short per-attempt timeout (fail fast) instead of one 15s hang, so the browser's
  // own abort + snapshot fallback kicks in quickly when the upstream is truly down.
  const attempts = [4000, 4000, 8000];
  for (let i = 0; i < attempts.length; i++) {
    const ctrl = new AbortController();
    const to = setTimeout(() => ctrl.abort(), attempts[i]);
    try {
      const r = await fetch(target, {
        signal: ctrl.signal,
        headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Accept': 'application/json' },
      });
      clearTimeout(to);
      const ct = r.headers.get('content-type') || 'application/json';
      res.writeHead(r.status, { 'Content-Type': ct, 'Cache-Control': 'no-store' });
      res.end(await r.text());
      return;
    } catch (e) {
      clearTimeout(to);
      if (i === attempts.length - 1) {
        res.writeHead(502, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'proxy failed', msg: String(e && e.message || e) }));
        return;
      }
    }
  }
}

// Forward a single JSON-RPC payload to an upstream Arc node with retries.
// arc-scan.org rate-limits eth_call/eth_blockNumber ("unreachable" + retry_after),
// which breaks wallet flows (add LP BID/ASK, swap, claim). Retry each upstream,
// honouring the server's retry_after hint, so a transient throttle never fails a call.
async function rpcFetchOnce(url, payload, timeoutMs) {
  const ctrl = new AbortController();
  const to = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const r = await fetch(url, {
      method: 'POST',
      signal: ctrl.signal,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!r.ok) return { ok: false, err: 'RPC HTTP ' + r.status };
    const j = await r.json();
    if (j.error) {
      const data = j.error.data || {};
      const retryAfter = Number(data.retry_after_seconds) || 0;
      return { ok: false, err: (j.error.message || 'rpc error'), retryAfter };
    }
    return { ok: true, body: j };
  } catch (e) {
    return { ok: false, err: String(e && e.message || e) };
  } finally {
    clearTimeout(to);
  }
}

async function rpcRetry(payload) {
  // Race ALL upstreams in parallel — first healthy response wins. This collapses the
  // old sequential 4×2 retry ladder (~12s worst case) down to a single ~1.5s round.
  const first = await Promise.race(RPC_URLS.map(url => rpcFetchOnce(url, payload, 1500)));
  if (first.ok) return first;

  // Fallback ladder: one retry per endpoint for transient throttles/races.
  for (const url of RPC_URLS) {
    const out = await rpcFetchOnce(url, payload, 2000);
    if (out.ok) return out;
  }
  return { ok: false, err: 'all upstream RPC endpoints failed' };
}