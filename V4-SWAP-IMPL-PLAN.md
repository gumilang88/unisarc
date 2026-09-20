# ARC Swap V4 — Implementasi (Plan Eksekusi)

## STATUS (19 Sep 2026)
Semua bahan teknis UDAH terpecahkan & terverifikasi on-chain. Tinggal IMPLEMENTASI swap end-to-end.

## Yang udah terverifikasi
1. PoolManager V4 ARC = `0x8366a39cc670b4001a1121b8f6a443a643e40951` (verified Blockscout, v0.8.26).
2. UniversalRouter = `0x4fca4a51ab4f23a7447b3284fbd7d73289a89fb1` (verified, standard uniswap universal-router).
3. PoolId = `keccak256(abi.encode(currency0, currency1, fee, tickSpacing, hooks))` — SOLVED.
4. PoolManager.swap selector = `0xf3cd914c`, PoolKey 5-tuple, SwapParams.
5. USDC native = 18 decimals (via `value`), ERC20 USDC `0x3600...0000` = 6 decimals.

## Command bytes UniversalRouter (standard)
- V3_SWAP_EXACT_IN = 0x00
- SWEEP = 0x04
- V4_SWAP = 0x10
- V4_INITIALIZE_POOL = 0x13
- V4_POSITION_MANAGER_CALL = 0x14
- FLAG_ALLOW_REVERT = 0x80

## execute() signature
`execute(bytes commands, bytes[] inputs, uint256 deadline) payable`

## Encoding V4_SWAP (0x10) — standard uniswap v4-periphery
Input = abi.encode(PoolKey, uint128 amountSpecified, uint128 amountLimit, bool zeroForOne, bytes hookData)
- PoolKey = (address currency0, address currency1, uint24 fee, int24 tickSpacing, address hooks) — 5 words
- amountSpecified < 0 = exact input (packed int128), amountLimit = min out (exact in) / max in (exact out)

## PLAN IMPLEMENTASI (urutan)
1. Baca slot0 pool via `extsload` (PM) buat dapet sqrtPriceX96 + tick + fee.
2. Compute poolId dari PoolKey.
3. Encode V4_SWAP command + inputs.
4. `eth_call` simulate dulu (tanpa kirim tx) buat dapet amountOut + cek revert reason.
5. Kirim tx `execute()` dengan `value` = native USDC amount (18 dec).
6. Tambah command `SWEEP` (0x04) di akhir buat narik sisa token ke recipient.

## Blocker tersisa
- RPC public ARC (warp-arc, blockdaemon) TIDAK support `debug_traceTransaction` → gak bisa baca revert reason.
- Butuh RPC paid (Alchemy/QuickNode ARC) ATAU trace via Blockscout internal (browser) buat debug revert.

## Catatan penting
- Executor `0x43d894e2` (selector `0xc1120e3d`) = router internal ARC, gak terverifikasi, encoding gelap. SKIP.
- Pakai UniversalRouter `execute()` langsung — verified + standard.
