# ARC Uniswap V4 PoolManager — Temuan Lengkap (19 Sep 2026)

## POOLID ENCODING (TERPECAHKAN)
poolId = keccak256(abi.encode(currency0, currency1, fee uint24, tickSpacing int24, hooks))
- 5 x 32 bytes (0xa0), currency sorted numerically.
- hooks BUKAN zero — tiap pool punya hooks address sendiri.

### Contoh verified (dari event Initialize 0xdd466e67):
ARGUS pool:
- currency0 = 0x69f3406adc05f06220a89d77202382aefd4be689
- currency1 = 0xece5ca8bf9220718e5727754026757512212cb3c (ARGUS)
- fee = 10000, tickSpacing = 200
- hooks = 0x4d5c8830857bd61f899a4227cb1ab19fe204a044
- poolId = 0x250312dbfaa1358c06f56a6d2e1593677aa47a51c2b5675e9ab3633dcd54a512

USDC pool:
- currency0 = 0x0f83e2cddaa1900e6e88dc35709f28210808ff3d
- currency1 = 0x3600000000000000000000000000000000000000 (USDC)
- fee = 10000, tickSpacing = 200
- hooks = 0x426cb51faaf417d2c0d2975619832e0ec4baa044
- poolId = 0xebb15d41347ac6425d18f16661dd5dbdb439801d26ac89f4ec69fc2b09b02ff4

## POOLMANAGER ADDRESS + ABI
- Address: 0x8366a39cc670b4001a1121b8f6a443a643e40951
- Terverifikasi Blockscout (partial match), compiler v0.8.26 cancun
- File: src/pkgs/v4-core/src/PoolManager.sol
- owner(): 0xbca30b5429935205037069cf5b8a165f55d05a75

## Function selector (dari ABI terverifikasi)
- swap((PoolKey),(SwapParams),bytes)      = 0xf3cd914c
- modifyLiquidity((PoolKey),(ModifyLiquidityParams),bytes) = 0x5a6bcfda
- initialize((PoolKey),uint160)           = 0x6276cbbe
- mint(address,uint256,uint256)           = 0x156e29f6  (add LP via ERC6909)
- burn(address,uint256,uint256)           = 0xf5298aca
- unlock(bytes)                           = 0x48c89491
- settle()                                = 0x11da60b4
- take(address,address,uint256)           = 0x0b0d9c09
- extsload(bytes32)                       = 0x1e2eaeaf  (read state)
- exttload(bytes32)                       = 0x9bf6645f
- balanceOf(address,uint256)              = 0x00fdd58e  (ERC6909 LP token)

## Struct definitions
PoolKey {
  address currency0;  // sorted
  address currency1;
  uint24 fee;
  int24 tickSpacing;
  address hooks;
}

SwapParams {
  int256 amountSpecified;   // <0 = exact input, >0 = exact output
  int24 tickSpacing;
  bool zeroForOne;
  uint160 sqrtPriceLimitX96;
  uint24 lpFeeOverride;
}

ModifyLiquidityParams {
  address owner;
  int24 tickLower;
  int24 tickUpper;
  int128 liquidityDelta;
  int24 tickSpacing;
  bytes32 salt;
}

## Cara baca state pool (slot0)
- Read via extsload(bytes32 slot) — bukan getSlot0.
- Pool.sol State struct layout: slot0 di offset tertentu (perlu decompile State.sol / Slot0.sol).
- Slot0 = { sqrtPriceX96, tick, protocolFee, lpFee, feeGrowthGlobal0X128, feeGrowthGlobal1X128 } (packed).

## SWAP EXECUTOR (reverse-engineered dari tx sukses)

### Executor 0x43d894e2 — selector 0xc1120e3d (10 arg, all 32 bytes)
```
swapExactInputSingle(UniversalRouter, PoolManager, token, amountIn, amountOut, recipient, deadline, fee, tickSpacing, hooks)
```
Arg index:
- [0] UniversalRouter = 0x4fca4a51ab4f23a7447b3284fbd7d73289a89fb1
- [1] PoolManager = 0x8366a39cc670b4001a1121b8f6a443a643e40951
- [2] token (yang DIBELI / output)
- [3] amountIn (USDC, exact input)
- [4] amountOut (token, output desired — exact output semantics)
- [5] recipient
- [6] deadline
- [7] fee (pool fee: USO=10000, BOARD=2500)
- [8] tickSpacing (USO=200, BOARD=50)
- [9] hooks (ZERO untuk pool tanpa custom hook)

### Contoh tx sukses:
1. USO swap (tx 0xe78de83d...): USDC->USO, fee=10000, ts=200, hooks=0. amountIn=19.8 USDC, amountOut=24.9 USO.
2. BOARD swap (tx 0xb63159bc...): token 0x08230708 (BOARD), fee=2500, ts=50, hooks=0. amountIn=1.14M, amountOut=580K.

### Alur swap (dari log receipt):
user --USDC--> executor 0x43d894e2 --USDC--> UniversalRouter --USDC--> PoolManager (swap) --token--> executor --token--> user

### Catatan penting:
- Executor 0x43d894e2 = router/aggregator custom (20KB, stateless, gak terverifikasi).
- **DECOMPILED (cast disassemble):** body `0xc1120e3d` di offset 0x2071. Argumen 10 (0x04..0x0124), tipe:
  [0] address (UR), [1] address (PM), [2] address (token), [3] uint256 (amountIn),
  [4] uint256 (amountOut), [5] address (recipient), [6] uint24 (fee), [7] uint256 (deadline),
  [8] int24 (tickSpacing), [9] address (hooks).
  Body nge-build PoolKey (MSTORE address0/address1/fee/tickSpacing/hooks di 0x20/0x40/0x60/0x80) lalu KECCAK256 → poolId, terus swap. Konfirmasi ini = swap V4.
- **`CALLVALUE ISZERO` branch** di 0x20f6: kalau value non-zero, ambil jalur berbeda. Swap pakai NATIVE USDC (value), BUKAN ERC20 approve.
- **Guard `CALLER == 0x5285211161ed2dc928cb062de5aac316247a2f1d`** ada di 2 function LAIN (offset 0x01ac, 0x14ee) — BUKAN di body `0xc1120e3d`. Jadi `0xc1120e3d` kemungkinan TANPA sender guard.
- **USDC = 6 decimals (ERC20 0x3600...0000)**; native gas = USDC (18 dec, pakai `value`).
- Swap amount kecil (0.05 USDC) REVERT gas ~26140 (revert awal, sebelum swap logic). Penyebab PASTI belum ketemu — perlu `debug_traceTransaction` (gak ada di RPC public).
- Revert reason gak bisa dibaca (node gak support debug_traceTransaction).
- Selector lain di executor (cast disassemble): `0x04e45aaf`=exactInputSingle(V3), `0x7ff36ab5`=swapExactETHForTokens(V2), `0x791ac947`=swapExactTokensForETH(V2), `0x24856bc3`=UR execute(V4), `0x3850c7bd`=slot0, `0xd06ca61f`=getAmountsOut(V2), `0x38a80c53`=exactInput(V3). → executor ini router universal V2+V3+V4.

## RPC yang jalan
- https://warp-arc-production.up.railway.app/rpc (eth_call/eth_getLogs OK)
- https://rpc.blockdaemon.mainnet.arc.io (dari skill)
- arc.drpc.org / rpc.arc-scan.org / thecusp = 403 rate-limit
- explorer.arc.io API = Cloudflare, harus via browser session.

## VERDICT: swap V4 itu implementable, tapi butuh:
1. ABI full (ada, 59 entries — dump di browser window.__PM_ABI)
2. UniversalRouter V4 (0x4fca4a51...) ATAU direct unlock()+callback pattern
3. Settlement (settle/take) + delta accounting — kompleks
4. Hook (0x4d5c88.../0x426cb5...) behavior unknown — bisa revert kalau hook custom
