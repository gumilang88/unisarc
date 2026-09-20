# ARC V4 Swap — Encoding FINAL (TERPECAHKAN 100%)

## Tx referensi SUKSES
`0xa883eb3fda15420915a19c80d199ef2267c1ae8b3969ee86fa2f1ff8384c7537`
46.795 USDC -> 688,498 ECOIN via UniversalRouter `execute()` (selector 0x3593564c)

## FULL ENCODING (dari source v4-periphery yang terverifikasi)

### execute(bytes commands, bytes[] inputs, uint256 deadline)
- commands = `[0x10]` (V4_SWAP)
- inputs = `[unlockData]`

### unlockData = abi.encode(bytes actions, bytes[] params)
- actions = `[0x06, 0x0c, 0x0f]` = SWAP_EXACT_IN_SINGLE, SETTLE_ALL, TAKE_ALL

### params[0] = ExactInputSingleParams (384 bytes, 12 words)
```
struct ExactInputSingleParams {
  PoolKey poolKey;          // (currency0, currency1, uint24 fee, int24 tickSpacing, address hooks)
  bool zeroForOne;
  uint128 amountIn;
  uint128 amountOutMinimum;
  uint256 minHopPriceX36;
  bytes hookData;
}
```
Layout word-by-word (12 words = 384 bytes):
```
[0]  = 0x20 (offset struct body)
[1]  = currency0 (USDC 0x3600...0000, 6 dec)
[2]  = currency1 (ECOIN 0x9e640ff7...)
[3]  = fee (10000)
[4]  = tickSpacing (200)
[5]  = hooks (0x64c7d402111565bacea59fc3fd12d150f8bc2044)
[6]  = zeroForOne (1 = true)
[7]  = amountIn (low 128) + amountOutMinimum (high 128, =0)
[8]  = minHopPriceX36 (0)
[9]  = hookData offset (0x140)
[10] = hookData len (0)
[11] = padding (0)
```

### params[1] = SETTLE_ALL = (currency=USDC, maxAmount=amountIn)
### params[2] = TAKE_ALL = (currency=ECOIN, minAmount=0)

## KEY FACTS
- USDC = 6 decimals (Circle native stablecoin, proxy impl 0xC6AD664a).
- amountIn di-encode 6 decimals (46795000 = 46.795 USDC).
- PoolManager 0x8366a39c, UniversalRouter 0x4fca4a51 (keduanya verified).
- PoolId = keccak256(currency0, currency1, fee, tickSpacing, hooks).
- Actions constants: SWAP_EXACT_IN_SINGLE=0x06, SETTLE_ALL=0x0c, TAKE_ALL=0x0f.

## STATUS TEST (19 Sep)
- Encoding udah byte-perfect match (calldata 1124 bytes identik tx sukses).
- Tapi swap 0.05 USDC masih REVERT gas ~35360 (masuk swap logic, revert di tengah).
- Bukan encoding, bukan allowance (udah approve UR + Permit2).
- Kemungkinan: amount 0.05 terlalu kecil (min liquidity/price-impact guard di hook 0x64c7d402).
- Revert reason gak bisa dibaca (custom error tanpa message, node gak support trace).

## NEXT STEP
- Coba amount lebih besar (0.1 USDC = max budget) buat konfirmasi min-liquidity theory.
- Atau RPC paid (Alchemy) buat trace revert reason.
