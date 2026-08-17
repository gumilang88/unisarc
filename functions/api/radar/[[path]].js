// Cloudflare Pages Function: /api/radar/* -> https://api.radardex.pro/*
// Mirrors the local server.js proxy so TVL/price/volume data is LIVE on prod.
const RADAR = 'https://api.radardex.pro';

export async function onRequest(context) {
  const { request } = context;

  // CORS (allow the dashboard origin; wildcard is fine for public read-only API)
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  const url = new URL(request.url);
  // Strip the /api/radar prefix. e.g. /api/radar/tokens?... -> /tokens?...
  let rest = url.pathname.slice('/api/radar'.length) + url.search;
  if (!rest.startsWith('/')) rest = '/tokens' + rest;

  const target = RADAR + rest;

  try {
    const upstream = await fetch(target, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json',
      },
    });
    const body = await upstream.text();
    const ct = upstream.headers.get('content-type') || 'application/json';
    return new Response(body, {
      status: upstream.status,
      headers: { ...corsHeaders, 'Content-Type': ct },
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: 'proxy failed', msg: String(e.message || e) }), {
      status: 502,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
}
