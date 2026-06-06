from accumulation_scanner.config import settings
from accumulation_scanner.core.math_utils import pct_change
from accumulation_scanner.core.models import Candle, Ticker


class MarketFilters:
    def reject_reason(self, ticker: Ticker, candles: list[Candle]) -> str | None:
        if ticker.volume_24h_ccy < settings.min_quote_volume_usdt:
            return "weak_liquidity"
        if ticker.spread_pct > settings.max_spread_pct:
            return "wide_spread"
        if len(candles) < 35:
            return "insufficient_history"
        recent = candles[-settings.recent_pump_lookback_days:]
        if len(recent) >= 2:
            recent_return = pct_change(recent[0].close, recent[-1].close)
            if recent_return > settings.max_recent_pump_pct:
                return "recent_pump"
        if candles[-1].close <= 0:
            return "invalid_price"
        return None
