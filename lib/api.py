"""Polymarket API client."""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Optional, Any, ClassVar
import httpx


@dataclass
class MarketInfo:
    """Market data with lazy loading support."""
    
    _api: ClassVar[Optional["PolymarketAPI"]] = None
    
    id: str
    question: str
    slug: str
    condition_id: str
    yes_token: str
    no_token: Optional[str]
    yes_price: float
    no_price: float
    total_volume: float
    daily_volume: float
    liquidity: float
    end_date: str
    is_active: bool
    is_closed: bool
    is_resolved: bool
    outcome: Optional[str]

    @classmethod
    def _parse(cls, raw: dict) -> MarketInfo:
        """Parse from raw API response."""
        tokens = json.loads(raw.get("clobTokenIds") or "[]")
        prices = json.loads(raw.get("outcomePrices") or "[0.5,0.5]")
        return cls(
            id=raw.get("id", ""),
            question=raw.get("question", ""),
            slug=raw.get("slug", ""),
            condition_id=raw.get("conditionId", ""),
            yes_token=tokens[0] if tokens else "",
            no_token=tokens[1] if len(tokens) > 1 else None,
            yes_price=float(prices[0]) if prices else 0.5,
            no_price=float(prices[1]) if len(prices) > 1 else 0.5,
            total_volume=float(raw.get("volume") or 0),
            daily_volume=float(raw.get("volume24hr") or 0),
            liquidity=float(raw.get("liquidity") or 0),
            end_date=raw.get("endDate") or "",
            is_active=raw.get("active", True),
            is_closed=raw.get("closed", False),
            is_resolved=raw.get("resolved", False),
            outcome=raw.get("outcome"),
        )

    @classmethod
    async def trending(cls, limit: int = 20) -> list[MarketInfo]:
        """Get trending markets by 24h volume."""
        api = cls._api or PolymarketAPI()
        return await api.list_markets(limit=limit)

    @classmethod
    async def search(cls, keyword: str, limit: int = 20) -> list[MarketInfo]:
        """Search markets by keyword."""
        api = cls._api or PolymarketAPI()
        return await api.find_markets(keyword, limit=limit)

    @classmethod
    async def get(cls, identifier: str) -> MarketInfo:
        """Get market by ID, slug, or URL."""
        api = cls._api or PolymarketAPI()
        if identifier.startswith("http"):
            slug = identifier.rstrip("/").split("/")[-1]
            return await api.get_market_by_slug(slug)
        elif identifier.isdigit():
            return await api.get_market_by_id(identifier)
        elif len(identifier) < 20:
            return await api.get_market_by_slug(identifier)
        return await api.get_market_by_id(identifier)

    @property
    def url(self) -> str:
        """Polymarket URL."""
        return f"https://polymarket.com/market/{self.slug}"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "question": self.question,
            "slug": self.slug,
            "yes_price": self.yes_price,
            "no_price": self.no_price,
            "volume_24h": self.daily_volume,
            "volume_total": self.total_volume,
            "liquidity": self.liquidity,
            "end_date": self.end_date,
            "yes_token_id": self.yes_token,
            "no_token_id": self.no_token,
            "condition_id": self.condition_id,
            "url": self.url,
        }


@dataclass
class EventInfo:
    """Event containing multiple markets."""
    
    _api: ClassVar[Optional["PolymarketAPI"]] = None
    
    id: str
    title: str
    slug: str
    description: str
    markets: list[MarketInfo] = field(default_factory=list)

    @classmethod
    def _parse(cls, raw: dict) -> EventInfo:
        """Parse from raw API response."""
        return cls(
            id=raw.get("id", ""),
            title=raw.get("title", ""),
            slug=raw.get("slug", ""),
            description=raw.get("description", ""),
            markets=[MarketInfo._parse(m) for m in raw.get("markets", [])],
        )

    @classmethod
    async def list(cls, limit: int = 20) -> list[EventInfo]:
        """List active events."""
        api = cls._api or PolymarketAPI()
        return await api.list_events(limit=limit)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "markets": [m.to_dict() for m in self.markets[:5]],
        }


class PolymarketAPI:
    """Low-level API client."""
    
    BASE_URL = "https://gamma-api.polymarket.com"

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout
        # Register this instance for class methods
        MarketInfo._api = self
        EventInfo._api = self

    async def _request(self, endpoint: str, params: dict = None) -> Any:
        """Execute GET request."""
        async with httpx.AsyncClient(timeout=self._timeout) as http:
            resp = await http.get(f"{self.BASE_URL}{endpoint}", params=params)
            resp.raise_for_status()
            return resp.json()

    async def list_markets(self, limit: int = 20, sort_by: str = "volume24hr") -> list[MarketInfo]:
        """List active markets."""
        data = await self._request("/markets", {
            "closed": "false",
            "limit": limit,
            "order": sort_by,
            "ascending": "false",
        })
        return [MarketInfo._parse(m) for m in data]

    async def find_markets(self, keyword: str, limit: int = 20) -> list[MarketInfo]:
        """Find markets matching keyword."""
        data = await self._request("/markets", {
            "closed": "false",
            "limit": 500,
            "order": "volume24hr",
            "ascending": "false",
        })
        kw = keyword.lower()
        matches = []
        for item in data:
            text = f"{item.get('question', '')} {item.get('slug', '')}".lower()
            if kw in text:
                matches.append(MarketInfo._parse(item))
                if len(matches) >= limit:
                    break
        return matches

    async def get_market_by_id(self, market_id: str) -> MarketInfo:
        """Fetch market by ID."""
        data = await self._request(f"/markets/{market_id}")
        return MarketInfo._parse(data)

    async def get_market_by_slug(self, slug: str) -> MarketInfo:
        """Fetch market by slug."""
        data = await self._request("/markets", {"slug": slug})
        if not data:
            raise ValueError(f"Market not found: {slug}")
        return MarketInfo._parse(data[0])

    async def list_events(self, limit: int = 20) -> list[EventInfo]:
        """List active events."""
        data = await self._request("/events", {
            "closed": "false",
            "limit": limit,
            "order": "volume24hr",
            "ascending": "false",
        })
        return [EventInfo._parse(e) for e in data]
