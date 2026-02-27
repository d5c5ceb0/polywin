"""Gas fee estimation for Polygon transactions.

Provides gas cost estimates for different transaction types on Polymarket.
Used to calculate minimum profitable position sizes for hedging strategies.

Gas estimation formula:
    gas_cost_usd = gas_units * gas_price_gwei * 1e-9 * pol_price_usd

Example (split transaction):
    300,000 gas * 50 gwei * 1e-9 * $0.40 = $0.006 per split
"""

import os
import httpx

# =============================================================================
# POLYGON GAS CONFIGURATION
# =============================================================================

# Fallback gas price if API call fails (gwei)
# Range: 30-100 gwei normally, can spike to 500+ during congestion
DEFAULT_GAS_PRICE_GWEI = 50

# Fallback POL token price in USD
DEFAULT_POL_PRICE_USD = 0.40

# Polygon RPC endpoint for gas price queries
# Uses same default as wallet_manager.py
DEFAULT_POLYGON_RPC_URL = "https://polygon.drpc.org"
POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL", DEFAULT_POLYGON_RPC_URL)

# Cache for gas price (to avoid too many RPC calls)
_gas_price_cache: dict = {"price_gwei": None, "timestamp": 0}
_pol_price_cache: dict = {"price_usd": None, "timestamp": 0}

# Cache TTL in seconds
GAS_PRICE_CACHE_TTL = 60  # 1 minute
POL_PRICE_CACHE_TTL = 300  # 5 minutes

# =============================================================================
# GAS LIMITS BY TRANSACTION TYPE
# =============================================================================

# Gas limits for different Polymarket operations
GAS_LIMITS = {
    # CTF split: USDC -> YES + NO tokens
    "split": 300_000,
    
    # CTF merge: YES + NO tokens -> USDC
    "merge": 250_000,
    
    # CTF redeem: Winning tokens -> USDC (after resolution)
    "redeem": 200_000,
    
    # ERC20 approve (one-time setup)
    "approve": 50_000,
    
    # CLOB order placement (off-chain, no gas)
    "clob_order": 0,
    
    # Token transfer
    "transfer": 65_000,
}

# =============================================================================
# HEDGE TRANSACTION COSTS
# =============================================================================

# A hedge portfolio requires these transactions:
# 1. Split for target market (USDC -> YES + NO)
# 2. Split for cover market (USDC -> YES + NO)
# 3. (Optional) Sell unwanted sides on CLOB (no gas, but has fees)
# 4. Redeem winning position after resolution

HEDGE_TRANSACTIONS = {
    "entry": ["split", "split"],           # 2 splits to enter hedge
    "exit_win": ["redeem"],                 # 1 redeem if we win
    "exit_partial": ["redeem", "redeem"],   # 2 redeems if both positions pay
}


# =============================================================================
# DYNAMIC PRICE FETCHING
# =============================================================================


import time


def get_current_gas_price() -> float:
    """
    Get current gas price from Polygon RPC.
    
    Returns gas price in gwei, falls back to default if API fails.
    Results are cached for GAS_PRICE_CACHE_TTL seconds.
    """
    global _gas_price_cache
    
    now = time.time()
    if _gas_price_cache["price_gwei"] is not None:
        if now - _gas_price_cache["timestamp"] < GAS_PRICE_CACHE_TTL:
            return _gas_price_cache["price_gwei"]
    
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(
                POLYGON_RPC_URL,
                json={
                    "jsonrpc": "2.0",
                    "method": "eth_gasPrice",
                    "params": [],
                    "id": 1,
                },
            )
            resp.raise_for_status()
            result = resp.json()
            
            # Convert from wei (hex) to gwei
            gas_price_wei = int(result["result"], 16)
            gas_price_gwei = gas_price_wei / 1e9
            
            _gas_price_cache["price_gwei"] = gas_price_gwei
            _gas_price_cache["timestamp"] = now
            
            return gas_price_gwei
            
    except Exception:
        # Fall back to default on any error
        return DEFAULT_GAS_PRICE_GWEI


def get_current_pol_price() -> float:
    """
    Get current POL token price in USD.
    
    Uses CoinGecko API, falls back to default if API fails.
    Results are cached for POL_PRICE_CACHE_TTL seconds.
    """
    global _pol_price_cache
    
    now = time.time()
    if _pol_price_cache["price_usd"] is not None:
        if now - _pol_price_cache["timestamp"] < POL_PRICE_CACHE_TTL:
            return _pol_price_cache["price_usd"]
    
    try:
        with httpx.Client(timeout=5.0) as client:
            # CoinGecko free API (no key required, but rate limited)
            resp = client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": "matic-network",  # POL is still listed as MATIC
                    "vs_currencies": "usd",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            
            pol_price = data["matic-network"]["usd"]
            
            _pol_price_cache["price_usd"] = pol_price
            _pol_price_cache["timestamp"] = now
            
            return pol_price
            
    except Exception:
        # Fall back to default on any error
        return DEFAULT_POL_PRICE_USD


def get_live_prices() -> tuple[float, float]:
    """
    Get current gas price and POL price.
    
    Returns:
        Tuple of (gas_price_gwei, pol_price_usd)
    """
    return get_current_gas_price(), get_current_pol_price()


# =============================================================================
# GAS COST CALCULATION
# =============================================================================


def calculate_gas_cost_usd(
    gas_units: int,
    gas_price_gwei: float | None = None,
    pol_price_usd: float | None = None,
    use_live_prices: bool = False,
) -> float:
    """
    Calculate gas cost in USD.
    
    Args:
        gas_units: Gas units consumed
        gas_price_gwei: Gas price in gwei (None = use default or live)
        pol_price_usd: POL token price in USD (None = use default or live)
        use_live_prices: If True, fetch live prices from APIs
    
    Returns:
        Gas cost in USD
    """
    if use_live_prices:
        if gas_price_gwei is None:
            gas_price_gwei = get_current_gas_price()
        if pol_price_usd is None:
            pol_price_usd = get_current_pol_price()
    else:
        if gas_price_gwei is None:
            gas_price_gwei = DEFAULT_GAS_PRICE_GWEI
        if pol_price_usd is None:
            pol_price_usd = DEFAULT_POL_PRICE_USD
    
    pol_cost = gas_units * gas_price_gwei * 1e-9
    return pol_cost * pol_price_usd


def estimate_transaction_cost(
    tx_type: str,
    gas_price_gwei: float | None = None,
    pol_price_usd: float | None = None,
    use_live_prices: bool = False,
) -> float:
    """
    Estimate cost for a specific transaction type.
    
    Args:
        tx_type: Transaction type (split, merge, redeem, etc.)
        gas_price_gwei: Gas price in gwei (None = use default or live)
        pol_price_usd: POL token price in USD (None = use default or live)
        use_live_prices: If True, fetch live prices from APIs
    
    Returns:
        Estimated cost in USD
    """
    gas_limit = GAS_LIMITS.get(tx_type, 0)
    return calculate_gas_cost_usd(gas_limit, gas_price_gwei, pol_price_usd, use_live_prices)


def estimate_hedge_entry_cost(
    gas_price_gwei: float | None = None,
    pol_price_usd: float | None = None,
    use_live_prices: bool = False,
) -> float:
    """
    Estimate total gas cost to enter a hedge position.
    
    Includes 2 split transactions (one for target, one for cover).
    
    Args:
        gas_price_gwei: Gas price in gwei (None = use default or live)
        pol_price_usd: POL token price in USD (None = use default or live)
        use_live_prices: If True, fetch live prices from APIs
    
    Returns:
        Total entry gas cost in USD
    """
    # Get prices once to use for all transactions
    if use_live_prices:
        if gas_price_gwei is None:
            gas_price_gwei = get_current_gas_price()
        if pol_price_usd is None:
            pol_price_usd = get_current_pol_price()
    else:
        if gas_price_gwei is None:
            gas_price_gwei = DEFAULT_GAS_PRICE_GWEI
        if pol_price_usd is None:
            pol_price_usd = DEFAULT_POL_PRICE_USD
    
    total = 0.0
    for tx_type in HEDGE_TRANSACTIONS["entry"]:
        total += estimate_transaction_cost(tx_type, gas_price_gwei, pol_price_usd)
    return total


def estimate_hedge_total_cost(
    gas_price_gwei: float | None = None,
    pol_price_usd: float | None = None,
    use_live_prices: bool = False,
) -> float:
    """
    Estimate total gas cost for a complete hedge cycle (entry + exit).
    
    Assumes worst case: entry (2 splits) + exit (1 redeem).
    
    Args:
        gas_price_gwei: Gas price in gwei (None = use default or live)
        pol_price_usd: POL token price in USD (None = use default or live)
        use_live_prices: If True, fetch live prices from APIs
    
    Returns:
        Total gas cost in USD
    """
    # Get prices once
    if use_live_prices:
        if gas_price_gwei is None:
            gas_price_gwei = get_current_gas_price()
        if pol_price_usd is None:
            pol_price_usd = get_current_pol_price()
    else:
        if gas_price_gwei is None:
            gas_price_gwei = DEFAULT_GAS_PRICE_GWEI
        if pol_price_usd is None:
            pol_price_usd = DEFAULT_POL_PRICE_USD
    
    entry_cost = estimate_hedge_entry_cost(gas_price_gwei, pol_price_usd)
    exit_cost = estimate_transaction_cost("redeem", gas_price_gwei, pol_price_usd)
    return entry_cost + exit_cost


def calculate_min_position_size(
    expected_profit_per_dollar: float,
    gas_cost_usd: float | None = None,
    use_live_prices: bool = False,
) -> float | None:
    """
    Calculate minimum position size to be profitable after gas.
    
    Args:
        expected_profit_per_dollar: Expected profit per $1 of position (before gas)
        gas_cost_usd: Total gas cost (defaults to hedge entry cost)
        use_live_prices: If True, fetch live prices for gas estimation
    
    Returns:
        Minimum position size in USD, or None if never profitable
    """
    if gas_cost_usd is None:
        gas_cost_usd = estimate_hedge_entry_cost(use_live_prices=use_live_prices)
    
    if expected_profit_per_dollar <= 0:
        return None  # Never profitable
    
    return gas_cost_usd / expected_profit_per_dollar


# =============================================================================
# DEFAULT VALUES FOR COVERAGE MODULE
# =============================================================================

# Pre-calculated default gas cost for hedge entry (2 splits)
# Used by coverage.py for min_position_size calculation
ESTIMATED_HEDGE_GAS_USD = estimate_hedge_entry_cost()


def get_gas_summary(use_live_prices: bool = False) -> dict:
    """
    Get summary of current gas estimates.
    
    Args:
        use_live_prices: If True, fetch live gas price and POL price from APIs
    
    Returns:
        Dict with gas price, POL price, and estimated costs for each tx type
    """
    if use_live_prices:
        gas_price = get_current_gas_price()
        pol_price = get_current_pol_price()
    else:
        gas_price = DEFAULT_GAS_PRICE_GWEI
        pol_price = DEFAULT_POL_PRICE_USD
    
    return {
        "gas_price_gwei": gas_price,
        "pol_price_usd": pol_price,
        "is_live": use_live_prices,
        "split_cost_usd": estimate_transaction_cost("split", gas_price, pol_price),
        "merge_cost_usd": estimate_transaction_cost("merge", gas_price, pol_price),
        "redeem_cost_usd": estimate_transaction_cost("redeem", gas_price, pol_price),
        "hedge_entry_cost_usd": estimate_hedge_entry_cost(gas_price, pol_price),
        "hedge_total_cost_usd": estimate_hedge_total_cost(gas_price, pol_price),
    }
