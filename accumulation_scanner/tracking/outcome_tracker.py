from __future__ import annotations

from datetime import datetime, timezone
from accumulation_scanner.config import settings
from accumulation_scanner.core.math_utils import pct_change
from accumulation_scanner.core.models import SignalOutcome
from accumulation_scanner.exchange.okx_public_client import OKXPublicClient
from accumulation_scanner.storage.repository import Repository


class OutcomeTracker:
    horizons = (7, 14, 30, 60)

    def __init__(self, repo: Repository, client: OKXPublicClient):
        self.repo = repo
        self.client = client

    async def evaluate_due_outcomes(self) -> dict:
        now = datetime.now(timezone.utc)
        evaluated = 0
        skipped = 0
        for signal in self.repo.pending_outcome_signals():
            created = datetime.fromisoformat(signal["created_at"])
            age_days = (now - created).days
            for horizon in self.horizons:
                if age_days < horizon:
                    continue
                candles = await self.client.get_candles(signal["inst_id"], settings.candle_bar, max(90, horizon + 10))
                if len(candles) < horizon + 1:
                    skipped += 1
                    continue
                entry_price = candles[-horizon - 1].close
                future = candles[-horizon:]
                final_price = future[-1].close
                max_high = max(c.high for c in future)
                min_low = min(c.low for c in future)
                future_return = pct_change(entry_price, final_price)
                max_gain = pct_change(entry_price, max_high)
                max_drawdown = pct_change(entry_price, min_low)
                verdict = self._verdict(future_return, max_gain, max_drawdown)
                self.repo.save_outcome(signal["inst_id"], SignalOutcome(
                    signal_id=signal["id"], horizon_days=horizon,
                    future_return_pct=round(future_return, 2), max_gain_pct=round(max_gain, 2),
                    max_drawdown_pct=round(max_drawdown, 2), verdict=verdict,
                    evaluated_at=now,
                ))
                evaluated += 1
        return {"evaluated": evaluated, "skipped": skipped}

    def _verdict(self, ret: float, max_gain: float, max_dd: float) -> str:
        if max_gain >= 35 and max_dd > -25:
            return "Excellent Signal"
        if max_gain >= 20 and ret > 5:
            return "Good Signal"
        if ret > 0 and max_dd > -18:
            return "Neutral Positive"
        if max_dd <= -25:
            return "Failed Risk"
        return "Weak Signal"
