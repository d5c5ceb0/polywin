---
name: polywin
description: "Browse Polymarket prediction markets, view order books, check prices, place trades."
metadata: {"openclaw":{"emoji":"📊","homepage":"https://polymarket.com","primaryEnv":"POLYMARKET_PRIVATE_KEY","requires":{"bins":["uv","polymarket"],"env":["POLYMARKET_PRIVATE_KEY"]},"install":[{"id":"uv-brew","kind":"brew","formula":"uv","bins":["uv"],"label":"Install uv (brew)"},{"id":"polymarket-brew","kind":"brew","tap":"Polymarket/polymarket-cli https://github.com/Polymarket/polymarket-cli","formula":"polymarket","bins":["polymarket"],"label":"Install polymarket CLI (brew)"}]},"clawdbot":{"emoji":"📊","homepage":"https://polymarket.com","primaryEnv":"POLYMARKET_PRIVATE_KEY","requires":{"bins":["uv","polymarket"],"env":["POLYMARKET_PRIVATE_KEY"]},"install":[{"id":"uv-brew","kind":"brew","formula":"uv","bins":["uv"],"label":"Install uv (brew)"},{"id":"polymarket-brew","kind":"brew","tap":"Polymarket/polymarket-cli https://github.com/Polymarket/polymarket-cli","formula":"polymarket","bins":["polymarket"],"label":"Install polymarket CLI (brew)"}]}}
---

# Polywin - Polymarket Trading Skill

Browse and trade on Polymarket prediction markets.

> ⚠️ **IMPORTANT FOR AGENTS:**
> - **DO NOT** call the `polymarket` binary directly.
> - **DO NOT** modify any files in this skill directory.
> - All commands go through: `uv run python scripts/polywin.py <command> ...`

## Architecture

Polymarket uses a **Proxy Wallet** system (Gnosis Safe) for gasless trading:

| Component | Address | Purpose |
|-----------|---------|---------|
| **EOA** | Your private key address | Signs transactions |
| **Proxy Wallet** | Derived from EOA | Holds funds, executes trades |

- **Funds**: Always in Proxy Wallet (USDC.e)
- **Gas (MATIC)**: In EOA for approvals
- **Signature Type**: `gnosis-safe` (default)

## Quick Start

```bash
cd {baseDir}
uv sync

# Browse trending markets (no wallet needed)
uv run python scripts/polywin.py markets trending -n 10

# Search markets
uv run python scripts/polywin.py markets search "bitcoin"

# Show help
uv run python scripts/polywin.py --help
```

## Setup for Trading

### 1. Set Environment Variable

```bash
export POLYMARKET_PRIVATE_KEY="0x..."  # Your EVM private key
```

### 2. Check Wallet Status

```bash
uv run python scripts/polywin.py wallet status
```

Output:
```
🔑 EOA Address:   0x...
📍 Proxy Address: 0x...  ← Your trading wallet
📝 Signature:     gnosis-safe

💰 USDC.e Balance: $0.00
📋 Approvals:      ⚠️ Not set
```

### 3. Deposit Funds

```bash
uv run python scripts/polywin.py wallet deposit
```

**Important:**
- Send **USDC.e** to **Proxy Address** (NOT EOA!)
- Send **MATIC** to **EOA** (for gas fees)
- Use Polygon network
- USDC.e contract: `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174`

### 4. Set Approvals (One-time)

```bash
uv run python scripts/polywin.py wallet approve
```

Requires MATIC in EOA for gas.

## Commands Reference

All commands use the unified entry point:
```bash
uv run python scripts/polywin.py <command> [subcommand] [options]
```

### Markets

| Subcommand | Description |
|------------|-------------|
| `trending` | Top markets by 24h volume |
| `search <query>` | Search markets by keyword |
| `list` | List markets with filters |
| `details <id>` | Get market details (JSON) |
| `events` | List events/groups |

**Examples:**
```bash
# Trending markets
uv run python scripts/polywin.py markets trending -n 10

# Search
uv run python scripts/polywin.py markets search "election"

# List with filters
uv run python scripts/polywin.py markets list -n 20 --tag politics
uv run python scripts/polywin.py markets list --active true --order volume_num

# Market details
uv run python scripts/polywin.py markets details <market_id_or_slug>

# Events
uv run python scripts/polywin.py markets events -n 5
```

**Options:**
- `-n/--limit` - Number of results
- `-f/--full` - Show full questions and URLs
- `-j/--json` - JSON output

**List Filters:**
- `--order` - Sort by: `volume_num`, `liquidity`, `start_date`, `end_date`, `created_at`
- `--ascending` - Sort ascending
- `--active` - Filter by active status (true/false)
- `--closed` - Filter by closed status (true/false)
- `--tag` - Filter by tag
- `--slug` - Filter by slug
- `--offset` - Pagination offset

### Portfolio

| Subcommand | Description |
|------------|-------------|
| `summary` | Portfolio overview (default) |
| `positions` | Current open positions |
| `closed` | Closed/settled positions |
| `trades` | Trade history |
| `balance` | USDC.e and token balances |
| `orders` | Open orders |

**Examples:**
```bash
# Portfolio summary
uv run python scripts/polywin.py portfolio summary
uv run python scripts/polywin.py portfolio  # Same as summary

# Current positions
uv run python scripts/polywin.py portfolio positions
uv run python scripts/polywin.py portfolio positions -n 20

# Closed positions
uv run python scripts/polywin.py portfolio closed

# Trade history
uv run python scripts/polywin.py portfolio trades -n 50

# Balances
uv run python scripts/polywin.py portfolio balance
uv run python scripts/polywin.py portfolio balance --asset-type conditional --token <token_id>

# Open orders
uv run python scripts/polywin.py portfolio orders
```

### Wallet

| Subcommand | Description |
|------------|-------------|
| `status` | Show addresses, balance, approvals |
| `deposit` | Show deposit instructions |
| `approve` | Set contract approvals |

**Examples:**
```bash
uv run python scripts/polywin.py wallet status
uv run python scripts/polywin.py wallet deposit
uv run python scripts/polywin.py wallet approve
uv run python scripts/polywin.py wallet approve --force  # Re-approve
```

### Trade

| Subcommand | Description |
|------------|-------------|
| `buy <token_id> <price> <size>` | Place limit buy order |
| `sell <token_id> <price> <size>` | Place limit sell order |
| `market-buy <token_id> <amount>` | Place market buy order |
| `market-sell <token_id> <amount>` | Place market sell order |
| `cancel <order_id>` | Cancel specific order |
| `cancel-all` | Cancel all orders |
| `orders` | List open orders |
| `trades` | List trade history |

**Trading Rules:**
| Rule | Requirement |
|------|-------------|
| Price range | `0.01` to `0.99` |
| Price precision | Max 2 decimal places (e.g., `0.50`, `0.43`) |
| Min order amount | **$1** (price × size ≥ 1) |

**Examples:**
```bash
# Limit orders (price × size must be ≥ $1)
uv run python scripts/polywin.py trade buy <yes_token_id> 0.50 2    # $1.00 ✓
uv run python scripts/polywin.py trade sell <no_token_id> 0.40 3   # $1.20 ✓

# ❌ Invalid examples:
# trade buy <token> 0.435 5   # Price has 3 decimals (max 2)
# trade buy <token> 0.40 1    # Amount $0.40 < $1 minimum

# Market orders
uv run python scripts/polywin.py trade market-buy <token_id> 10
uv run python scripts/polywin.py trade market-sell <token_id> 5

# Cancel orders
uv run python scripts/polywin.py trade cancel <order_id>
uv run python scripts/polywin.py trade cancel-all

# View orders/trades
uv run python scripts/polywin.py trade orders
uv run python scripts/polywin.py trade trades
```

### CLOB (Order Book)

| Subcommand | Description |
|------------|-------------|
| `book <token_id>` | Show order book |
| `midpoint <token_id>` | Get midpoint price |
| `spread <token_id>` | Get bid-ask spread |

**Examples:**
```bash
uv run python scripts/polywin.py clob book <token_id>
uv run python scripts/polywin.py clob midpoint <token_id>
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POLYMARKET_PRIVATE_KEY` | **Yes** | - | EVM private key (hex, 0x prefix) |
| `POLYMARKET_SIGNATURE_TYPE` | No | `gnosis-safe` | Signature type: `eoa`, `proxy`, `gnosis-safe` |

## Common Workflows

### Check Market and Place Trade

```bash
# 1. Find market
uv run python scripts/polywin.py markets search "bitcoin"

# 2. Get details (includes token IDs)
uv run python scripts/polywin.py markets details <market_id>

# 3. Check order book
uv run python scripts/polywin.py clob book <yes_token_id>

# 4. Place order
uv run python scripts/polywin.py trade buy <yes_token_id> 0.55 10
```

### Monitor Portfolio

```bash
# Portfolio summary (positions, orders, balance)
uv run python scripts/polywin.py portfolio summary

# Detailed positions
uv run python scripts/polywin.py portfolio positions

# Trade history
uv run python scripts/polywin.py portfolio trades

# Check wallet status
uv run python scripts/polywin.py wallet status
```

## Short Aliases

For convenience, short aliases are available:

| Alias | Command |
|-------|---------|
| `m` | `markets` |
| `p` | `portfolio` |
| `w` | `wallet` |
| `t` | `trade` |

```bash
uv run python scripts/polywin.py m trending -n 5
uv run python scripts/polywin.py p summary
uv run python scripts/polywin.py w status
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Approvals not set" | Run `polywin.py wallet approve` (needs MATIC) |
| "Insufficient balance" | Deposit USDC.e to **Proxy Address** |
| "Transaction failed" | Check MATIC balance in EOA |
| "Market not found" | Use market slug or numeric ID |
| "Price has N decimal places" | Use max 2 decimals (e.g., `0.50` not `0.505`) |
| "min size: $1" | Increase size so `price × size ≥ $1` |

## Install Dependencies

```bash
cd {baseDir}
uv sync
```

## Links

- [Polymarket](https://polymarket.com)
- [Polymarket CLI](https://github.com/Polymarket/polymarket-cli)
- [API Documentation](https://docs.polymarket.com)
