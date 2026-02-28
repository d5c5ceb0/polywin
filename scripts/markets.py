#!/usr/bin/env python3
"""Market browsing commands."""

import sys
import json
import asyncio
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.api import MarketInfo, EventInfo, PolymarketAPI
from scripts import cli


def fmt_price(price: float) -> str:
    """Format price as cents."""
    return f"{int(price * 100)}¢"


def fmt_vol(vol: float) -> str:
    """Format volume."""
    if vol >= 1_000_000:
        return f"${vol / 1_000_000:.1f}M"
    elif vol >= 1_000:
        return f"${vol / 1_000:.0f}K"
    return f"${vol:.0f}"


def fmt_date(date_str: str) -> str:
    """Format date as YYYY-MM-DD."""
    if not date_str:
        return "-"
    return date_str[:10]  # e.g. "2026-01-31"


def print_table(markets: list[MarketInfo], full: bool = False):
    """Print markets as table."""
    print(f"{'ID':<10} {'Question':<36} {'YES':>4} {'NO':>4} {'Vol24h':>7} {'Total':>7} {'End':>10}")
    print("-" * 95)
    for m in markets:
        q = m.question if full else (m.question[:34] + "…" if len(m.question) > 34 else m.question)
        print(f"{m.id[:10]:<10} {q:<36} {fmt_price(m.yes_price):>4} {fmt_price(m.no_price):>4} {fmt_vol(m.daily_volume):>7} {fmt_vol(m.total_volume):>7} {fmt_date(m.end_date):>10}")
    
    if full:
        print()
        for m in markets:
            print(f"  {m.id}: {m.url}")


async def cmd_trending(args):
    """Show trending markets."""
    PolymarketAPI()  # Initialize API
    markets = await MarketInfo.trending(limit=args.limit)
    if args.json:
        print(json.dumps([m.to_dict() for m in markets], indent=2))
    else:
        print_table(markets, args.full)


async def cmd_search(args):
    """Search markets."""
    PolymarketAPI()
    markets = await MarketInfo.search(args.query, limit=args.limit)
    if not markets:
        print(f"No markets found: {args.query}")
        return 1
    if args.json:
        print(json.dumps([m.to_dict() for m in markets], indent=2))
    else:
        print_table(markets, args.full)


async def cmd_details(args):
    """Show market details."""
    PolymarketAPI()
    try:
        m = await MarketInfo.get(args.market_id)
    except Exception as e:
        print(f"Error: {e}")
        return 1

    print(json.dumps({
        **m.to_dict(),
        "status": {
            "active": m.is_active,
            "closed": m.is_closed,
            "resolved": m.is_resolved,
            "outcome": m.outcome,
        },
    }, indent=2))


async def cmd_events(args):
    """Show events."""
    PolymarketAPI()
    events = await EventInfo.list(limit=args.limit)

    if args.json:
        print(json.dumps([e.to_dict() for e in events], indent=2))
    else:
        for e in events:
            print(f"\n{e.title}")
            print(f"  Slug: {e.slug}")
            for m in e.markets[:3]:
                q = m.question if args.full else (m.question[:55] + "…" if len(m.question) > 55 else m.question)
                print(f"    {fmt_price(m.yes_price):>4} {q}")


def cmd_list(args):
    """List markets using native CLI (supports all filters)."""
    cmd_args = ["markets", "list"]
    
    if args.limit:
        cmd_args.extend(["--limit", str(args.limit)])
    if args.offset:
        cmd_args.extend(["--offset", str(args.offset)])
    if args.order:
        cmd_args.extend(["--order", args.order])
    if args.ascending:
        cmd_args.append("--ascending")
    if args.active is not None:
        cmd_args.extend(["--active", str(args.active).lower()])
    if args.closed is not None:
        cmd_args.extend(["--closed", str(args.closed).lower()])
    if args.tag:
        cmd_args.extend(["--tag", args.tag])
    if args.slug:
        cmd_args.extend(["--slug", args.slug])
    
    return cli.run(cmd_args, json_output=args.json)


def main():
    parser = argparse.ArgumentParser(description="Browse Polymarket")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("trending", help="Trending markets")
    p.add_argument("-n", "--limit", type=int, default=20)
    p.add_argument("-f", "--full", action="store_true")
    p.add_argument("-j", "--json", action="store_true")

    p = sub.add_parser("search", help="Search markets")
    p.add_argument("query")
    p.add_argument("-n", "--limit", type=int, default=20)
    p.add_argument("-f", "--full", action="store_true")
    p.add_argument("-j", "--json", action="store_true")

    p = sub.add_parser("details", help="Market details")
    p.add_argument("market_id")

    p = sub.add_parser("events", help="List events")
    p.add_argument("-n", "--limit", type=int, default=10)
    p.add_argument("-f", "--full", action="store_true")
    p.add_argument("-j", "--json", action="store_true")

    # Native CLI list command with full filter support
    p = sub.add_parser("list", help="List markets (native CLI with filters)")
    p.add_argument("-n", "--limit", type=int, default=10)
    p.add_argument("--offset", type=int)
    p.add_argument("--order", choices=["volume_num", "liquidity", "start_date", "end_date", "created_at"])
    p.add_argument("--ascending", action="store_true")
    p.add_argument("--active", type=lambda x: x.lower() == "true", metavar="BOOL")
    p.add_argument("--closed", type=lambda x: x.lower() == "true", metavar="BOOL")
    p.add_argument("--tag", help="Filter by tag")
    p.add_argument("--slug", help="Filter by slug")
    p.add_argument("-j", "--json", action="store_true", default=True)

    args = parser.parse_args()

    # Sync handlers (native CLI)
    sync_handlers = {
        "list": cmd_list,
    }

    # Async handlers (API)
    async_handlers = {
        "trending": cmd_trending,
        "search": cmd_search,
        "details": cmd_details,
        "events": cmd_events,
    }

    if args.cmd in sync_handlers:
        return sync_handlers[args.cmd](args)
    if args.cmd in async_handlers:
        return asyncio.run(async_handlers[args.cmd](args))
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main() or 0)
