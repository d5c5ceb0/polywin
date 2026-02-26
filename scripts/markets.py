#!/usr/bin/env python3
"""Market browsing commands."""

import sys
import json
import asyncio
import argparse
from datetime import datetime
from pathlib import Path

# Add parent to path for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.gamma_client import GammaClient


def format_price(price: float) -> str:
    """Format price as cents."""
    return f"${price:.2f}"


def format_volume(volume: float) -> str:
    """Format volume in human-readable form."""
    if volume >= 1_000_000:
        return f"${volume / 1_000_000:.1f}M"
    elif volume >= 1_000:
        return f"${volume / 1_000:.1f}K"
    else:
        return f"${volume:.0f}"


def format_end_date(end_date: str) -> str:
    """Format end date in human-readable form."""
    if not end_date:
        return "N/A"
    try:
        # Parse ISO format date
        dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        delta = dt - now

        if delta.days < 0:
            return "Ended"
        elif delta.days == 0:
            hours = delta.seconds // 3600
            if hours == 0:
                return "<1h"
            return f"{hours}h"
        elif delta.days < 7:
            return f"{delta.days}d"
        elif delta.days < 30:
            return f"{delta.days // 7}w"
        elif delta.days < 365:
            return f"{delta.days // 30}mo"
        else:
            return dt.strftime("%Y-%m")
    except (ValueError, TypeError):
        return end_date[:10] if len(end_date) >= 10 else end_date


def format_market_row(market, truncate: int = 0) -> dict:
    """Format market for display. Set truncate=0 for full question."""
    question = market.question
    if truncate > 0 and len(question) > truncate:
        question = question[:truncate] + "..."
    return {
        "id": market.id,
        "question": question,
        "yes": format_price(market.yes_price),
        "no": format_price(market.no_price),
        "volume_24h": format_volume(market.volume_24h),
        "volume_total": format_volume(market.volume),
        "end_date": market.end_date,
        "ends_in": format_end_date(market.end_date),
    }


async def cmd_trending(args):
    """Show trending markets."""
    client = GammaClient()
    markets = await client.get_trending_markets(limit=args.limit)

    if args.json:
        # JSON output: full questions for agent consumption
        print(json.dumps([format_market_row(m) for m in markets], indent=2))
    else:
        # Terminal output: truncate unless --full
        print(f"{'ID':<12} {'Question':<52} {'YES':>6} {'NO':>6} {'24h Vol':>10} {'Ends':>6}")
        print("-" * 100)
        for m in markets:
            question = m.question if args.full else (m.question[:50] + "..." if len(m.question) > 50 else m.question)
            ends = format_end_date(m.end_date)
            print(f"{m.id[:12]:<12} {question:<52} {format_price(m.yes_price):>6} {format_price(m.no_price):>6} {format_volume(m.volume_24h):>10} {ends:>6}")


async def cmd_new(args):
    """Show newest markets."""
    client = GammaClient()
    markets = await client.get_new_markets(limit=args.limit)

    if args.json:
        # JSON output: full questions for agent consumption
        print(json.dumps([format_market_row(m) for m in markets], indent=2))
    else:
        # Terminal output: truncate unless --full
        print(f"{'ID':<12} {'Question':<52} {'YES':>6} {'NO':>6} {'24h Vol':>10} {'Ends':>6}")
        print("-" * 100)
        for m in markets:
            question = m.question if args.full else (m.question[:50] + "..." if len(m.question) > 50 else m.question)
            ends = format_end_date(m.end_date)
            print(f"{m.id[:12]:<12} {question:<52} {format_price(m.yes_price):>6} {format_price(m.no_price):>6} {format_volume(m.volume_24h):>10} {ends:>6}")


async def cmd_search(args):
    """Search markets by keyword."""
    client = GammaClient()
    markets = await client.search_markets(args.query, limit=args.limit)

    if not markets:
        print(f"No markets found for: {args.query}")
        return 1

    if args.json:
        # JSON output: full questions for agent consumption
        print(json.dumps([format_market_row(m) for m in markets], indent=2))
    else:
        # Terminal output: truncate unless --full
        print(f"{'ID':<12} {'Question':<52} {'YES':>6} {'NO':>6} {'24h Vol':>10} {'Ends':>6}")
        print("-" * 100)
        for m in markets:
            question = m.question if args.full else (m.question[:50] + "..." if len(m.question) > 50 else m.question)
            ends = format_end_date(m.end_date)
            print(f"{m.id[:12]:<12} {question:<52} {format_price(m.yes_price):>6} {format_price(m.no_price):>6} {format_volume(m.volume_24h):>10} {ends:>6}")


async def cmd_details(args):
    """Show market details."""
    client = GammaClient()

    try:
        if args.market_id.startswith("http"):
            # Extract slug from URL
            slug = args.market_id.rstrip("/").split("/")[-1]
            market = await client.get_market_by_slug(slug)
        elif args.market_id.isdigit():
            # Numeric IDs are Gamma market IDs
            market = await client.get_market(args.market_id)
        elif len(args.market_id) < 20:
            # Assume it's a slug
            market = await client.get_market_by_slug(args.market_id)
        else:
            # Assume it's an ID
            market = await client.get_market(args.market_id)
    except Exception as e:
        print(f"Error: {e}")
        return 1

    result = {
        "id": market.id,
        "question": market.question,
        "slug": market.slug,
        "condition_id": market.condition_id,
        "prices": {
            "yes": market.yes_price,
            "no": market.no_price,
        },
        "tokens": {
            "yes_token_id": market.yes_token_id,
            "no_token_id": market.no_token_id,
        },
        "volume": {
            "24h": market.volume_24h,
            "total": market.volume,
        },
        "liquidity": market.liquidity,
        "status": {
            "active": market.active,
            "closed": market.closed,
            "resolved": market.resolved,
            "outcome": market.outcome,
        },
        "end_date": market.end_date,
        "url": f"https://polymarket.com/event/{market.slug}",
    }

    print(json.dumps(result, indent=2))


async def cmd_events(args):
    """Show events/groups with markets."""
    client = GammaClient()
    events = await client.get_events(limit=args.limit)

    if args.json:
        # JSON output: full questions for agent consumption
        result = []
        for e in events:
            result.append({
                "id": e.id,
                "title": e.title,
                "slug": e.slug,
                "markets": [format_market_row(m) for m in e.markets[:5]],
            })
        print(json.dumps(result, indent=2))
    else:
        for e in events:
            print(f"\n{e.title}")
            print(f"  Slug: {e.slug}")
            print(f"  Markets: {len(e.markets)}")
            for m in e.markets[:3]:
                question = m.question if args.full else (m.question[:70] + "..." if len(m.question) > 70 else m.question)
                print(f"    - {question} (YES: {format_price(m.yes_price)})")


def main():
    parser = argparse.ArgumentParser(description="Market browsing")
    parser.add_argument("--json", action="store_true", help="JSON output")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Trending
    trending_parser = subparsers.add_parser("trending", help="Show trending markets")
    trending_parser.add_argument("--limit", type=int, default=20, help="Number of markets")
    trending_parser.add_argument("--full", action="store_true", help="Show full question text")

    # New
    new_parser = subparsers.add_parser("new", help="Show newest markets")
    new_parser.add_argument("--limit", type=int, default=20, help="Number of markets")
    new_parser.add_argument("--full", action="store_true", help="Show full question text")

    # Search
    search_parser = subparsers.add_parser("search", help="Search markets")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=20, help="Number of results")
    search_parser.add_argument("--full", action="store_true", help="Show full question text")

    # Details
    details_parser = subparsers.add_parser("details", help="Market details")
    details_parser.add_argument("market_id", help="Market ID, slug, or URL")

    # Events
    events_parser = subparsers.add_parser("events", help="Show events/groups")
    events_parser.add_argument("--limit", type=int, default=10, help="Number of events")
    events_parser.add_argument("--full", action="store_true", help="Show full question text")

    args = parser.parse_args()

    if args.command == "trending":
        return asyncio.run(cmd_trending(args))
    elif args.command == "new":
        return asyncio.run(cmd_new(args))
    elif args.command == "search":
        return asyncio.run(cmd_search(args))
    elif args.command == "details":
        return asyncio.run(cmd_details(args))
    elif args.command == "events":
        return asyncio.run(cmd_events(args))
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)
