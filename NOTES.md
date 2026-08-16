# LiquidHub — LP Dashboard (ARC Mainnet)

Liquidity Provider dashboard: posisi LP, add/remove liquidity, monitor pool, claim rewards.

## Ringkasan
- **File**: `index.html` (static single-file, no build/deps)
- **Chain**: ARC mainnet, chainId 5042 (0x13b2)
- **RPC**: `https://arc-mainnet.infura.io/v3/b6bf7d3508c941499b10025c0776eaf8`
- **Fallback RPC**: `https://robinlaunchpad.com/rpc/arc/v1`, `https://arc-rpc.stakeme.pro/`
- **Explorer**: `https://arc-mainnet.cloud.blockscout.com`
- **Tema**: pixel retro (bg ungu #3c1154, cyan #3ddad8, kuning #ffbe39, border hitam 4px + shadow 8px). Font: Space Grotesk (heading) + Inter (body).
- **Git**: repo terpisah (bukan parent /home/gumilang). Commit local, BELUM di-push.

## Cara jalanin
```bash
cd /home/gumilang/lp-dashboard-arc-mainnet
python3 -m http.server 3011
# buka http://localhost:3011/index.html
```
Server terakhir jalan di PID 35935 (mungkin mati setelah WSL restart — tinggal relaunch).

## Empat tab (SPA dalam 1 file)
1. **Positions** — list posisi LP, portfolio chart (SVG candles), filter, stat (total value/fees/share/APR)
2. **Add LP** — pilih pool, deposit token A/B, detail price/reserves/share/fees, slippage
3. **Monitor** — TVL/volume/fees semua pool, sparkline per pool
4. **Rewards** — total claimable, claim per-pool / claim all

## STATUS PENTING — LP masih SIMULASI
Chain + RPC udah MAINNET, TAPI data LP masih fake/simulasi karena contract belum diisi:

```js
const CFG = {
  ...
  factory: '',   // <-- KOSONG. Isi alamat UniswapV3/V2 factory Arc mainnet utk live pool scan
  router:  '',   // <-- KOSONG. Isi alamat router utk add/remove real
  reward:  '',   // <-- KOSONG. claimRewards
}
```

- `const LIVE = !!(CFG.factory && CFG.router)` → begitu dua-duanya diisi, mode jadi LIVE.
- Selama kosong: tampilkan data simulasi (localStorage persist), tanpa badge "DEMO DATA" (sudah dihilangkan per request).
- Add/remove/claim sekarang = simulasikan + save ke localStorage (`liquidityhub-pos`).

## TODO besok
1. Isi `factory` + `router` + `reward` (alamat Uniswap Arc mainnet) → mode LIVE beneran.
2. Opsional: tarik data pool real dari Uniswap V3 Arc (atau RadarDex) ganti data simulasi.
3. Opsional: deploy ke Cloudflare Pages (pola usdc-troll/usdc-stonks, GH Actions wrangler-action).
4. Belum ada package.json → verification = node --check + browser, bukan npm test.
