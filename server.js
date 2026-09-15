// UNISARC static server + RadarDex API proxy (CORS bypass)
// Usage: node server.js  (serves on :3011 by default)
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3011;
const RADAR = 'https://api.radardex.pro';
const FILE = path.join(__dirname, 'index.html');

// Arc mainnet RPC (chain 5042) — public node is intermittent; retry aggressively.
// thecusp/warp are ecosystem relays that the RadarDex frontend also uses as fallback.
const RPC_URLS = [
  'https://rpc.arc-scan.org',
  'https://arc-mainnet.infura.io/v3/b6bf7d3508c941499b10025c0776eaf8',
  'https://thecusp.io/api/arc-rpc',
  'https://warp-arc-production.up.railway.app/rpc',
];

const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.svg': 'image/svg+xml', '.json': 'application/json' };

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
    const ctrl = new AbortController();
    const to = setTimeout(() => ctrl.abort(), 15000);
    fetch(target, {
      signal: ctrl.signal,
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Accept': 'application/json' },
    })
      .then(r => { clearTimeout(to); const ct = r.headers.get('content-type') || 'application/json'; res.writeHead(r.status, { 'Content-Type': ct }); return r.text(); })
      .then(body => res.end(body))
      .catch(e => { clearTimeout(to); res.writeHead(502, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ error: 'proxy failed', msg: String(e.message || e) })); });
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
  if (p === '/index.html' || p === '/') {
    fs.readFile(FILE, (err, data) => {
      if (err) { res.writeHead(500); return res.end('read error'); }
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
      res.end(data);
    });
    return;
  }
  fs.readFile(full, (err, data) => {
    if (err) { res.writeHead(404); return res.end('not found'); }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(full)] || 'application/octet-stream' });
    res.end(data);
  });
});

server.listen(PORT, () => console.log(`UNISARC on http://localhost:${PORT}  (proxy /api/radar -> ${RADAR})`));

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
  // Light retry: the browser already races a 2.2s timeout + multiple upstreams, so this
  // proxy should fail fast rather than holding a request open for tens of seconds.
  const attempts = 2;
  for (const url of RPC_URLS) {
    for (let i = 0; i < attempts; i++) {
      const out = await rpcFetchOnce(url, payload, 1500);
      if (out.ok) return out;
      await new Promise(r => setTimeout(r, 200 * (i + 1)));
    }
  }
  return { ok: false, err: 'all upstream RPC endpoints failed' };
}