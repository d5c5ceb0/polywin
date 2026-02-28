#!/usr/bin/env python3
"""Polywin - Polymarket Trading Skill for OpenClaw.

Usage:
    polywin <command> [subcommand] [options]

Commands:
    markets     Browse and search markets
    portfolio   View positions, balances, trades
    wallet      Wallet management
    trade       Place and manage orders
    clob        Order book operations
    data        On-chain data queries
"""

import sys
import subprocess
from pathlib import Path

# Load .env file from skill root directory
try:
    from dotenv import load_dotenv
    SKILL_DIR = Path(__file__).parent.parent
    load_dotenv(SKILL_DIR / ".env")
except ImportError:
    pass

SCRIPT_DIR = Path(__file__).parent


def run_script(script_name: str, args: list[str]) -> int:
    """Run a script with arguments."""
    script_path = SCRIPT_DIR / f"{script_name}.py"
    if not script_path.exists():
        print(f"Error: Script not found: {script_path}")
        return 1
    cmd = [sys.executable, str(script_path)] + args
    result = subprocess.run(cmd)
    return result.returncode


def print_help():
    """Print help message."""
    print("""
Polywin - Polymarket Trading Skill

Usage: uv run python scripts/polywin.py <command> [subcommand] [options]

Commands:
  markets     Browse and search prediction markets
    trending    Top markets by 24h volume
    search      Search markets by keyword
    list        List markets with filters
    details     Get market details (JSON)
    events      List events/groups

  portfolio   View your portfolio
    summary     Portfolio overview (default)
    positions   Current open positions
    closed      Closed/settled positions
    trades      Trade history
    balance     USDC.e and token balances
    orders      Open orders

  wallet      Wallet management
    status      Show addresses, balance, approvals
    deposit     Show deposit instructions
    approve     Set contract approvals

  trade       Place and manage orders
    buy         Place limit buy order
    sell        Place limit sell order
    market-buy  Place market buy order
    market-sell Place market sell order
    cancel      Cancel order
    cancel-all  Cancel all orders
    orders      View open orders
    trades      View trade history

  clob        Order book operations
    book        Show order book
    midpoint    Get midpoint price
    spread      Get bid-ask spread

  data        On-chain data (pass-through to CLI)

Options:
  -h, --help     Show this help
  -v, --version  Show version

Examples:
  polywin markets trending -n 10
  polywin markets search "bitcoin"
  polywin portfolio summary
  polywin wallet status
  polywin trade buy <token_id> 0.55 10
""")


def main():
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    # Help
    if cmd in ["help", "--help", "-h"]:
        print_help()
        return 0
    
    # Version
    if cmd in ["version", "--version", "-v"]:
        print("Polywin v0.2.0")
        return 0
    
    # Route to appropriate script
    script_map = {
        "markets": "markets",
        "market": "markets",      # Alias
        "m": "markets",           # Short alias
        "portfolio": "portfolio",
        "p": "portfolio",         # Short alias
        "wallet": "wallet",
        "w": "wallet",            # Short alias
        "trade": "trade",
        "t": "trade",             # Short alias
        "clob": "clob",
        "data": "data",
    }
    
    if cmd in script_map:
        script_name = script_map[cmd]
        
        # Handle aliases with implicit subcommand
        if cmd == "market" and args:
            # market <id> -> markets details <id>
            args = ["details"] + args
        
        return run_script(script_name, args)
    
    # Unknown command - try passing to CLI directly
    from scripts import cli
    no_json = {"shell", "setup", "upgrade"}
    use_json = cmd not in no_json
    return cli.run(sys.argv[1:], json_output=use_json)


if __name__ == "__main__":
    sys.exit(main())
