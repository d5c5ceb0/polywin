#!/usr/bin/env python3
"""PolyWin CLI - Polymarket trading skill for OpenClaw.

Usage:
    polywin markets trending
    polywin markets search "election"
    polywin market <id>
    polywin wallet status
    polywin wallet approve
    polywin buy <market_id> YES 50
    polywin sell <market_id> YES
    polywin positions
    polywin hedge scan
    polywin hedge scan --query "election"
    polywin hedge analyze <id1> <id2>
"""

import sys
import subprocess
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
SCRIPT_DIR = Path(__file__).parent


def ensure_dependencies():
    """Check and install dependencies if needed."""
    try:
        import httpx
        import web3
        import dotenv
        return True
    except ImportError:
        print("Installing dependencies...")
        result = subprocess.run(
            ["uv", "sync"],
            cwd=SKILL_DIR,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"Failed to install dependencies: {result.stderr}")
            return False
        print("Dependencies installed successfully.")
        return True


# Ensure dependencies before importing anything else
if not ensure_dependencies():
    sys.exit(1)

# Now safe to import dotenv
from dotenv import load_dotenv
load_dotenv(SKILL_DIR / ".env")


def run_script(script_name: str, args: list[str]) -> int:
    """Run a script with arguments."""
    script_path = SCRIPT_DIR / f"{script_name}.py"
    if not script_path.exists():
        print(f"Error: Script not found: {script_path}")
        return 1

    cmd = [sys.executable, str(script_path)] + args
    result = subprocess.run(cmd)
    return result.returncode


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    # Route commands to appropriate scripts
    if command == "markets":
        return run_script("markets", args)

    elif command == "market":
        # Shortcut: polywin market <id> -> polywin markets details <id>
        if not args:
            print("Usage: polywin market <market_id>")
            return 1
        return run_script("markets", ["details"] + args)

    elif command == "wallet":
        return run_script("wallet", args)

    elif command == "balance":
        # Shortcut: polywin balance -> wallet status
        return run_script("wallet", ["status"])

    elif command == "buy":
        # Shortcut: polywin buy <id> YES 50 -> trade buy <id> YES 50
        return run_script("trade", ["buy"] + args)

    elif command == "sell":
        # Shortcut: polywin sell <id> YES -> trade sell <id> YES
        return run_script("trade", ["sell"] + args)

    elif command == "positions":
        return run_script("positions", args)

    elif command == "hedge":
        return run_script("hedge", args)

    elif command == "help" or command == "--help" or command == "-h":
        print(__doc__)
        print("Commands:")
        print("  markets trending           Show trending markets by volume")
        print("  markets new                Show newest markets by creation time")
        print("  markets search <query>     Search markets by keyword")
        print("  markets events             Show events with multiple markets")
        print("  market <id>                Show market details")
        print("")
        print("  wallet status              Show wallet status and balances")
        print("  wallet approve             Set Polymarket contract approvals (one-time)")
        print("  balance                    Show wallet balances (shortcut)")
        print("")
        print("  buy <market_id> YES <amt>  Buy YES position for $amt")
        print("  buy <market_id> NO <amt>   Buy NO position for $amt")
        print("")
        print("  sell <market_id> YES       Sell all YES tokens")
        print("  sell <market_id> NO        Sell all NO tokens")
        print("  sell <market_id> YES --amount 50  Sell 50 YES tokens")
        print("")
        print("  positions                  List positions from CLOB API")
        print("")
        print("  hedge scan                 Scan trending markets for hedges")
        print("  hedge scan --query <q>     Scan markets matching query")
        print("  hedge analyze <id1> <id2>  Analyze pair for hedging relationship")
        print("")
        print("Environment Variables:")
        print("  CHAINSTACK_NODE            Polygon RPC URL (required for trading)")
        print("  OPENROUTER_API_KEY         OpenRouter API key (required for hedge)")
        print("  POLYWIN_PRIVATE_KEY        EVM private key (required for trading)")
        print("")
        print("Examples:")
        print("  polywin markets trending")
        print("  polywin markets search 'trump'")
        print("  polywin market will-trump-win-2028")
        print("  polywin wallet status")
        print("  polywin buy abc123 YES 50")
        print("  polywin positions")
        print("  polywin hedge scan")
        print("  polywin hedge scan --query 'election'")
        return 0

    elif command == "version" or command == "--version" or command == "-v":
        print("PolyWin v0.1.0")
        return 0

    else:
        print(f"Unknown command: {command}")
        print("Run 'polywin help' for usage")
        return 1


if __name__ == "__main__":
    sys.exit(main())
