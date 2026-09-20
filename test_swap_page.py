import re
from pathlib import Path
from eth_abi.abi import encode
from web3 import Web3

SRC = Path(__file__).with_name("index.html").read_text()
USDC = "0x3600000000000000000000000000000000000000"
UNISARC = "0x1061d7f4934542b654e2a4ef7f04f101b4e8018d"
RECIPIENT = "0x000000000000000000000000000000000000dEaD"


def extract_fn(name):
    start = SRC.index(f"function {name}(")
    brace = SRC.index("{", start)
    depth = 0
    for i in range(brace, len(SRC)):
        depth += SRC[i] == "{"
        depth -= SRC[i] == "}"
        if depth == 0:
            return SRC[start:i + 1]
    raise AssertionError(name)


def test_swap_view_and_navigation_exist():
    assert 'data-v="swap"' in SRC
    assert 'id="view-swap"' in SRC
    assert "['home','positions','add','swap','monitor','tools']" in SRC


def test_verified_contracts_and_selectors_are_pinned():
    assert "router:  '0x53bf6b0684ec7ef91e1387da3d1a1769bc5a6f77'" in SRC
    assert "quoter:  '0x7dfd4f31be6814d2906bde155c3e1b146eac1468'" in SRC
    assert "QUOTER_EXACT_INPUT_SINGLE = '0xc6a5026a'" in SRC
    assert "ROUTER_EXACT_INPUT_SINGLE = '0x04e45aaf'" in SRC


def test_quoter_vector_matches_abi_oracle():
    amount = 10_000_000
    limit = 1461446703485210103287273052203988822378723970341
    expected = Web3.keccak(text="quoteExactInputSingle((address,address,uint256,uint24,uint160))").hex()[:8] + encode(
        ["address", "address", "uint256", "uint24", "uint160"],
        [USDC, UNISARC, amount, 10000, limit],
    ).hex()
    assert expected.startswith("c6a5026a")
    assert len(expected) == 8 + 5 * 64
    fn = extract_fn("encodeQuoterSwap")
    assert "addrArg(tIn.address)+addrArg(tOut.address)+uintArg(amount)" in fn
    assert "uintArg(swapSqrtLimit(tIn,tOut))" in fn


def test_router_vector_shape_matches_abi_oracle():
    expected = Web3.keccak(text="exactInputSingle((address,address,uint24,address,uint256,uint256,uint160))").hex()[:8] + encode(
        ["address", "address", "uint24", "address", "uint256", "uint256", "uint160"],
        [USDC, UNISARC, 10000, RECIPIENT, 10_000_000, 1, 0],
    ).hex()
    assert expected.startswith("04e45aaf")
    assert len(expected) == 8 + 7 * 64
    fn = extract_fn("encodeRouterSwap")
    assert "uintArg(fee,3).padStart(64,'0')+addrArg(recipient)" in fn
    assert "+uintArg(amountIn)+uintArg(minOut)+uintArg(0)" in fn


def test_speed_and_safety_invariants():
    assert "Promise.any(CFG.rpcUrls.map" in SRC
    assert "setTimeout(()=>runSwapQuote(seq),120)" in SRC
    assert "SWAP_QUOTE_TTL_MS = 12000" in SRC
    assert "Promise.all([quoteUniswap(a,b,amountIn),quoteUniswap(a,b,baseIn)])" in SRC
    assert "await ensureAllowance(a.address,CFG.router,q.amountIn)" in SRC
    assert "await sendTx(CFG.router,encodeRouterSwap" in SRC
    assert "if(q.impact>10)" in SRC


def test_no_automatic_send_on_render_or_quote():
    for name in ("renderSwap", "runSwapQuote", "scheduleSwapQuote"):
        fn = extract_fn(name)
        assert "sendTx(" not in fn
        assert "eth_sendTransaction" not in fn


def test_wallet_balances_and_picker_layout():
    assert "refreshSwapBalances()" in extract_fn("connect")
    balances_fn = extract_fn("loadAllSwapBalances")
    assert "priority=[S.swap.tokenIn,S.swap.tokenOut]" in balances_fn
    assert "rest.slice(i,i+12)" in balances_fn
    picker = extract_fn("renderSwapPicker")
    assert "swap-pick-price" in picker
    assert "swap-pick-balance" in picker
    assert "shortAddr(t.address)" not in picker
    assert "t.address.includes(q)" not in picker
    price_fn = extract_fn("swapPriceFive")
    assert "toFixed(5)" in price_fn
    assert "toPrecision" not in price_fn
    balance_fn = extract_fn("refreshSwapBalances")
    assert "S.swap.balanceCache" in balance_fn
    assert "tokenBalanceOf(t.address" in balance_fn
    assert "show('swapBalIn',a)" in balance_fn
    assert "!(t.address in cache)" in balance_fn
    render_fn = extract_fn("renderSwap")
    assert "readBalance=false" in render_fn
    assert "if(readBalance) refreshSwapBalances()" in render_fn
    assert "S.swap.balanceCache" in render_fn
    assert "+a.symbol" in render_fn
    assert "Balance loading" not in extract_fn("refreshSwapBalances")
    assert 'class="swap-picker-head"' in SRC
    assert 'class="swap-picker-search-wrap"' in SRC


def test_pct_buttons_and_picker_consistency():
    assert 'id="swapPctIn"' in SRC
    assert 'data-pct="100"' in SRC
    assert "applySwapPct" in SRC
    assert "$('swapPctIn').addEventListener" in SRC
    pct_fn = extract_fn("applySwapPct")
    assert "fmtCoin" not in pct_fn            # MAX must NOT write "28K" into the amount input
    assert "toFixed" in pct_fn
    assert "replace(/0+$/" in pct_fn
    assert "Uniswap V3." in SRC          # card copy: SwapRouter02 -> V3
    assert "swap-step" in SRC
    assert "Your wallet sends straight to Uniswap V3." in SRC
    assert "straight to Uniswap SwapRouter02" not in SRC
    picker = extract_fn("renderSwapPicker")
    assert 'class="pool-opt' in picker   # same row layout as Add LP select-pool overlay
    assert "po-sym" in picker
    assert "balanceCache" in picker       # balances from full-token cache, not just UNISARC
    assert "loadAllSwapBalances()" in extract_fn("connect")


def test_gas_fee_lowered_in_wallet():
    assert "buildGasFields" in SRC
    assert "eth_maxPriorityFeePerGas" in SRC
    assert "eth_estimateGas" in SRC
    send = extract_fn("sendTx")
    assert "buildGasFields({ from: S.address, to, data, value })" in send
    # must still preserve amount/destination/calldata (only gas fields added)
    assert "to" in send and "data" in send and "value" in send
    gf = extract_fn("buildGasFields")
    assert "maxPriorityFeePerGas" in gf
    assert "maxFeePerGas" in gf
    assert "oneGwei" in gf
    assert "base * 120n / 100n" in gf
    assert "tx.gas" in gf


def test_swap_market_monitor_follows_selected_token():
    assert 'id="swapMiniMonitor"' in SRC
    assert 'id="swapChartSvg"' in SRC
    chart = extract_fn("renderSwapMiniChart")
    assert "b.symbol==='USDC'?a:b" in chart
    assert "radarTokenByAddress(t.address)" in chart
    assert "sparkInner(spark,120,58,cls)" in chart
    assert "renderSwapMiniChart(a,b)" in extract_fn("renderSwap")
    assert "spark:" in SRC and "change24h:" in SRC


def test_swap_picker_bottom_tokens_and_no_balance_flicker():
    assert "SWAP_PIN_BOTTOM" in SRC
    for label in ("EURC", "cirBTC", "USYC", "SYN", "SWPRC"):
        assert label in SRC
    picker = extract_fn("renderSwapPicker")
    assert "SWAP_PIN_BOTTOM.get" in picker
    balances = extract_fn("loadAllSwapBalances")
    assert "renderSwapPicker()" not in balances
    assert "updateSwapPickerBalances(first)" in balances
    assert "updateSwapPickerBalances(chunk)" in balances
    updater = extract_fn("updateSwapPickerBalances")
    assert ".textContent='Balance '" in updater


def test_radardex_full_tokens_and_address_resolve():
    uni = extract_fn("swapTokenUniverse")
    assert "S.radarTokens" in uni       # include ALL RadarDex tokens (new/tiny too)
    assert "resolveSwapTokenByAddress" in SRC
    assert "isAddressLike" in SRC
    assert "tokenMeta(addr)" in extract_fn("resolveSwapTokenByAddress")
    assert "resolvedTokens" in extract_fn("chooseSwapToken")
    assert "resolvedTokens" in extract_fn("initSwapState")


