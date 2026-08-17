# LiquidHub — LP Dashboard (ARC Mainnet, LIVE on-chain)

Liquidity provider dashboard untuk Uniswap V3 ARC Mainnet (chain 5042).

## Cara jalanin
```bash
cd /home/gumilang/lp-dashboard-arc-mainnet
node server.js        # → http://localhost:3011  (serve static + proxy /api/radar)
```
Default port 3011 (env PORT bisa ganti). Python http.server TIDAK cukup — butuh `node server.js` karena dashboard butuh proxy RadarDex (`/api/radar`) biar API-nya bisa diakses dari browser (API radardex CORS-block; proxy same-origin solusinya).

## Contract map (VERIFIED on-chain, 2026-08-17)
| Kontrak | Address |
|---|---|
| Uniswap V3 Factory (non-canonical) | `0xf0db7b58379503491d857db50ac9ece64c653918` |
| SwapRouter02 | `0x53bf6b0684ec7ef91e1387da3d1a1769bc5a6f77` |
| NonfungiblePositionManager (NFPM) | `0x39654A85A4C05127f5Fd6ED22CAeC077A0fB1377` |
| Quoter | `0x7dfd4f31be6814d2906bde155c3e1b146eac1468` |
| USDC (native) | `0x3600000000000000000000000000000000000000` |
| RPC publik eth_call | `https://rpc.arc-scan.org` |
| RPC infura (user) | `https://arc-mainnet.infura.io/v3/b6bf7d3508c941499b10025c0776eaf8` |

NFPM ditemukan via eth_getLogs event IncreaseLiquidity di block terakhir (bukan address canonical — canonical 0xC36442... KOSONG di Arc, JANGAN dipakai). totalSupply 4221.

## Fitur — SEMUA LIVE, NO DEMO
- **Monitor** — pool list live dari RadarDex via proxy (`/api/radar/tokens?sort=volume24&limit=200`), 60+ pool, filter liq>=$1400. TVL/vol/fees/APR dari data real.
- **Positions** — baca NFPM on-chain per wallet: balanceOf → tokenOfOwnerByIndex → positions(tokenId). Decode token0/token1/fee/tick range/liquidity(uint128)/owed fees. Value = pro-rata share dari pool TVL (anti float-explosion). Badge IN RANGE / OUT RANGE.
- **Claim** — NFPM.collect(tokenId) → real tx dari wallet (ambil fees owed).
- **Remove** — decreaseLiquidity + collect + burn (kalau 100%).
- **Add** — UI pilih pool + amount, user pilih posisi existing untuk increaseLiquidity (flow di tab Positions → Add).

## Catatan krusial (pitfall, jangan diulang)
1. **Buffer TIDAK ada di browser** — pakai TextDecoder/hexToString manual, bukan Buffer.from.
2. **Decode struct positions**: 12 slot × 32 byte. Token address = 40 hex TERAKHIR dari slot (bukan dari awal slot — 24 hex nol dulu).
3. **liquidity & owed = uint128** — mask `& ((1n<<128n)-1n)`; kalau dibaca 256-bit penuh value meledak jadi 1e43+.
4. **Estimasi value**: rumus V3 murni (L*(sb-sqrtP)/(sb*sqrtP)) overflow buat range lebar — pakai pro-rata (pos.liquidity / pool.liquidity) × pool TVL dari RadarDex; fallback raw clamped.
5. **TICK parsing slot0**: word ke-2 = tick int24 → slice r[66:130] lalu BigInt.asIntN(24, ...).
6. **CORS** — api.radardex.pro block fetch browser (401/500 dengan Origin). Selalu lewat proxy server.
7. git repo terpisah di folder ini (jangan `git add -A` dari /home/gumilang).

## Testing wallet real tanpa connect
```js
// di browser console:
S.tokenMeta = {}; S.address = '<pemilik-nfpm-address>';
await loadPositionsUI();
```
Contoh owner yang punya 50 posisi: `0x630957cf4582bada8b583b5a9476a7108cfde0a4` (posisi #4-13, value ~$41K).