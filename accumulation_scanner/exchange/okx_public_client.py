from __future__ import annotations

from datetime import datetime, timezone
import httpx
from accumulation_scanner.config import settings
from accumulation_scanner.core.models import Candle, Ticker


class OKXPublicClient:
    """Public OKX market data client. No API keys. No execution."""

    def __init__(self, base_url: str | None = None, timeout: float = 20.0):
        self.base_url = (base_url or settings.okx_base_url).rstrip("/")
        self.timeout = timeout

    async def _get(self, path: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(f"{self.base_url}{path}", params=params)
            r.raise_for_status()
            payload = r.json()
            if payload.get("code") != "0":
                raise RuntimeError(f"OKX error {payload.get('code')}: {payload.get('msg')}")
            return payload

    async def get_spot_tickers(self) -> list[Ticker]:
        payload = await self._get("/api/v5/market/tickers", {"instType": "SPOT"})
        tickers: list[Ticker] = []
        for row in payload.get("data", []):
            inst_id = row.get("instId", "")
            if not inst_id.endswith("-USDT") and not inst_id.endswith("-USDC"):
                continue
            try:
                tickers.append(Ticker(
                    inst_id=inst_id,
                    last=float(row.get("last") or 0),
                    bid=float(row.get("bidPx") or 0),
                    ask=float(row.get("askPx") or 0),
                    volume_24h_ccy=float(row.get("volCcy24h") or 0),
                    volume_24h_base=float(row.get("vol24h") or 0),
                ))
            except ValueError:
                continue
        return tickers

    async def get_candles(self, inst_id: str, bar: str, limit: int) -> list[Candle]:
        payload = await self._get("/api/v5/market/candles", {"instId": inst_id, "bar": bar, "limit": str(limit)})
        candles: list[Candle] = []
        for row in payload.get("data", []):
            try:
                ts = datetime.fromtimestamp(int(row[0]) / 1000, tz=timezone.utc)
                candles.append(Candle(
                    ts=ts,
                    open=float(row[1]),
                    high=float(row[2]),
                    low=float(row[3]),
                    close=float(row[4]),
                    volume=float(row[5]),
                    volume_ccy=float(row[7]) if len(row) > 7 else float(row[5]) * float(row[4]),
                ))
            except (ValueError, IndexError):
                continue
        return list(reversed(candles))
