#!/usr/bin/env python3
"""Position tracking - fetches real-time positions from CLOB API."""

import sys
import json
import asyncio
import argparse
from pathlib import Path

# Add parent to path for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file from skill root directory
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from lib.gamma_client import GammaClient
from lib.wallet_manager import WalletManager
from lib.clob_client import ClobClientWrapper


async def cmd_list(args):
    """Fetch positions directly from CLOB API (on-chain data)."""
    wallet = WalletManager()

    if not wallet.is_unlocked:
        print("Error: No wallet configured")
        print("Set POLYWIN_PRIVATE_KEY environment variable.")
        return 1

    print(f"Fetching positions for {wallet.address}...")

    try:
        clob = ClobClientWrapper(
            wallet.get_unlocked_key(),
            wallet.address,
        )
        positions = clob.get_positions()

        if not positions:
            print("No positions found.")
            return 0

        # Enrich positions with market data from Gamma API
        gamma = GammaClient()
        enriched_positions = []
        
        # Cache markets to avoid repeated API calls
        markets_cache = {}
        
        for pos in positions:
            token_id = str(pos.get("asset", pos.get("token_id", "")))
            balance = float(pos.get("size", pos.get("balance", 0)))
            
            if balance <= 0:
                continue
            
            # Try to find market info for this token
            market_question = "Unknown market"
            side = "?"
            market_id = ""
            current_price = 0.0
            
            try:
                # Fetch markets if not cached
                if not markets_cache:
                    markets = await gamma.get_trending_markets(limit=200, include_ended=True)
                    for m in markets:
                        if m.yes_token_id:
                            markets_cache[m.yes_token_id] = (m, "YES")
                        if m.no_token_id:
                            markets_cache[m.no_token_id] = (m, "NO")
                
                if token_id in markets_cache:
                    m, side = markets_cache[token_id]
                    market_question = m.question
                    market_id = m.id
                    current_price = m.yes_price if side == "YES" else m.no_price
            except Exception:
                pass
            
            enriched_positions.append({
                "token_id": token_id,
                "balance": balance,
                "side": side,
                "market_id": market_id,
                "question": market_question,
                "current_price": current_price,
                "value": balance * current_price if current_price > 0 else 0,
            })

        if args.json:
            print(json.dumps(enriched_positions, indent=2))
        else:
            print(f"\n{'Side':<5} {'Balance':>10} {'Price':>8} {'Value':>10} {'Market'}")
            print("-" * 90)
            total_value = 0
            for pos in enriched_positions:
                side = pos["side"]
                balance = pos["balance"]
                price = pos["current_price"]
                value = pos["value"]
                question = pos["question"][:50] + "..." if len(pos["question"]) > 50 else pos["question"]
                
                price_str = f"${price:.2f}" if price > 0 else "?"
                value_str = f"${value:.2f}" if value > 0 else "?"
                
                print(f"{side:<5} {balance:>10.2f} {price_str:>8} {value_str:>10} {question}")
                total_value += value
            
            print("-" * 90)
            print(f"Total value: ${total_value:.2f}")

        return 0

    except Exception as e:
        print(f"Error fetching positions: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Position tracking (on-chain)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List (default)
    subparsers.add_parser("list", help="List positions from CLOB API")
    
    # Onchain (alias for list, for backward compatibility)
    subparsers.add_parser("onchain", help="List positions from CLOB API")

    args = parser.parse_args()

    # All commands go to the same function
    return asyncio.run(cmd_list(args))


if __name__ == "__main__":
    sys.exit(main() or 0)
