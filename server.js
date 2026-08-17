// LiquidHub static server + RadarDex API proxy (CORS bypass)
// Usage: node server.js  (serves on :3011 by default)
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3011;
const RADAR = 'https://api.radardex.pro';
const FILE = path.join(__dirname, 'index.html');

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

server.listen(PORT, () => console.log(`LiquidHub on http://localhost:${PORT}  (proxy /api/radar -> ${RADAR})`));