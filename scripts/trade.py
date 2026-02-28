#!/usr/bin/env python3
"""Trading commands (create-order, market-order, cancel)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts import cli


def main():
    """Run trading commands via clob."""
    # Map trade commands to clob subcommands
    if len(sys.argv) < 2:
        print("Usage: trade <buy|sell|cancel|orders>")
        return 1
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    if cmd == "buy":
        # trade buy <token> <price> <size> -> clob create-order --token <token> --side buy --price <price> --size <size>
        if len(args) < 3:
            print("Usage: trade buy <token_id> <price> <size>")
            return 1
        return cli.run([
            "clob", "create-order",
            "--token", args[0],
            "--side", "buy",
            "--price", args[1],
            "--size", args[2]
        ] + args[3:])
    
    elif cmd == "sell":
        if len(args) < 3:
            print("Usage: trade sell <token_id> <price> <size>")
            return 1
        return cli.run([
            "clob", "create-order",
            "--token", args[0],
            "--side", "sell",
            "--price", args[1],
            "--size", args[2]
        ] + args[3:])
    
    elif cmd == "market-buy":
        if len(args) < 2:
            print("Usage: trade market-buy <token_id> <amount>")
            return 1
        return cli.run([
            "clob", "market-order",
            "--token", args[0],
            "--side", "buy",
            "--amount", args[1]
        ] + args[2:])
    
    elif cmd == "market-sell":
        if len(args) < 2:
            print("Usage: trade market-sell <token_id> <amount>")
            return 1
        return cli.run([
            "clob", "market-order",
            "--token", args[0],
            "--side", "sell",
            "--amount", args[1]
        ] + args[2:])
    
    elif cmd == "cancel":
        return cli.run(["clob", "cancel"] + args)
    
    elif cmd == "cancel-all":
        return cli.run(["clob", "cancel-all"])
    
    elif cmd == "orders":
        return cli.run(["clob", "orders"] + args)
    
    elif cmd == "trades":
        return cli.run(["clob", "trades"] + args)
    
    else:
        print(f"Unknown trade command: {cmd}")
        print("Available: buy, sell, market-buy, market-sell, cancel, cancel-all, orders, trades")
        return 1


if __name__ == "__main__":
    sys.exit(main())
