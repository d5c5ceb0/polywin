#!/usr/bin/env python3
"""Portfolio commands - positions, balances, trades."""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts import cli


def run_cli(args: list[str], capture: bool = False) -> tuple[int, str]:
    """Run polymarket CLI and optionally capture output."""
    if not cli.check_installed():
        return 1, "polymarket CLI not installed"
    
    cmd = ["polymarket"]
    
    # Add default signature type if not set
    if not os.environ.get("POLYMARKET_SIGNATURE_TYPE"):
        cmd.extend(["--signature-type", cli.DEFAULT_SIGNATURE_TYPE])
    
    cmd.extend(["-o", "json"] + args)
    
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout
    else:
        result = subprocess.run(cmd)
        return result.returncode, ""


def get_wallet_address() -> str | None:
    """Get proxy wallet address."""
    code, output = run_cli(["wallet", "show"], capture=True)
    if code == 0 and output.strip():
        try:
            data = json.loads(output)
            return data.get("proxy_address") or data.get("address")
        except:
            pass
    return None


def cmd_positions(args):
    """Show current positions."""
    address = args.address or get_wallet_address()
    if not address:
        print("❌ Could not get wallet address. Set POLYMARKET_PRIVATE_KEY or provide --address")
        return 1
    
    cmd_args = ["data", "positions", address]
    if args.limit:
        cmd_args.extend(["--limit", str(args.limit)])
    
    return cli.run(cmd_args, json_output=True)


def cmd_closed(args):
    """Show closed positions."""
    address = args.address or get_wallet_address()
    if not address:
        print("❌ Could not get wallet address. Set POLYMARKET_PRIVATE_KEY or provide --address")
        return 1
    
    cmd_args = ["data", "closed-positions", address]
    if args.limit:
        cmd_args.extend(["--limit", str(args.limit)])
    
    return cli.run(cmd_args, json_output=True)


def cmd_trades(args):
    """Show trade history."""
    address = args.address or get_wallet_address()
    if not address:
        print("❌ Could not get wallet address. Set POLYMARKET_PRIVATE_KEY or provide --address")
        return 1
    
    cmd_args = ["data", "trades", address]
    if args.limit:
        cmd_args.extend(["--limit", str(args.limit)])
    
    return cli.run(cmd_args, json_output=True)


def cmd_balance(args):
    """Show balances."""
    cmd_args = ["clob", "balance"]
    
    if args.asset_type:
        cmd_args.extend(["--asset-type", args.asset_type])
    if args.token:
        cmd_args.extend(["--token", args.token])
    
    return cli.run(cmd_args, json_output=True)


def cmd_orders(args):
    """Show open orders."""
    cmd_args = ["clob", "orders"]
    
    if args.market:
        cmd_args.extend(["--market", args.market])
    
    return cli.run(cmd_args, json_output=True)


def cmd_summary(args):
    """Show portfolio summary."""
    address = args.address or get_wallet_address()
    if not address:
        print("❌ Could not get wallet address")
        return 1
    
    print(f"📊 Portfolio Summary for {address[:10]}...{address[-6:]}\n")
    
    # Balance
    print("💰 Balances:")
    code, output = run_cli(["clob", "balance", "--asset-type", "collateral"], capture=True)
    if code == 0:
        try:
            data = json.loads(output)
            balance = float(data.get("balance", 0))
            print(f"   USDC.e: ${balance:.2f}")
        except:
            print(f"   {output.strip()}")
    
    print()
    
    # Open orders
    print("📋 Open Orders:")
    code, output = run_cli(["clob", "orders"], capture=True)
    if code == 0:
        try:
            orders = json.loads(output)
            if orders:
                for o in orders[:5]:
                    side = o.get("side", "?").upper()
                    price = float(o.get("price", 0))
                    size = float(o.get("original_size", 0))
                    print(f"   {side} {size:.2f} @ {price:.2f}")
                if len(orders) > 5:
                    print(f"   ... and {len(orders) - 5} more")
            else:
                print("   No open orders")
        except:
            print(f"   {output.strip()}")
    
    print()
    
    # Positions
    print("📈 Positions:")
    code, output = run_cli(["data", "positions", address, "--limit", "5"], capture=True)
    if code == 0:
        try:
            positions = json.loads(output)
            if positions:
                for p in positions[:5]:
                    title = p.get("title", p.get("market", "Unknown"))[:40]
                    size = float(p.get("size", 0))
                    outcome = p.get("outcome", "?")
                    print(f"   {outcome}: {size:.2f} - {title}")
                if len(positions) > 5:
                    print(f"   ... and {len(positions) - 5} more")
            else:
                print("   No open positions")
        except:
            print(f"   {output.strip()}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Portfolio management - positions, balances, trades"
    )
    sub = parser.add_subparsers(dest="cmd")
    
    # positions
    p = sub.add_parser("positions", help="Show current positions")
    p.add_argument("-a", "--address", help="Wallet address (default: your proxy)")
    p.add_argument("-n", "--limit", type=int, default=50)
    
    # closed
    p = sub.add_parser("closed", help="Show closed positions")
    p.add_argument("-a", "--address", help="Wallet address")
    p.add_argument("-n", "--limit", type=int, default=50)
    
    # trades
    p = sub.add_parser("trades", help="Show trade history")
    p.add_argument("-a", "--address", help="Wallet address")
    p.add_argument("-n", "--limit", type=int, default=50)
    
    # balance
    p = sub.add_parser("balance", help="Show balances")
    p.add_argument("--asset-type", choices=["collateral", "conditional"], default="collateral")
    p.add_argument("--token", help="Token ID for conditional balance")
    
    # orders
    p = sub.add_parser("orders", help="Show open orders")
    p.add_argument("--market", help="Filter by market")
    
    # summary
    p = sub.add_parser("summary", help="Portfolio summary")
    p.add_argument("-a", "--address", help="Wallet address")
    
    args = parser.parse_args()
    
    handlers = {
        "positions": cmd_positions,
        "closed": cmd_closed,
        "trades": cmd_trades,
        "balance": cmd_balance,
        "orders": cmd_orders,
        "summary": cmd_summary,
    }
    
    if args.cmd in handlers:
        return handlers[args.cmd](args)
    
    # Default: show summary
    if not args.cmd:
        args.address = None
        return cmd_summary(args)
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
