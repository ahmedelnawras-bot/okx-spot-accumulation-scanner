from __future__ import annotations

from accumulation_scanner.config import settings
from accumulation_scanner.core.filters import MarketFilters
from accumulation_scanner.core.scoring import AccumulationScorer
from accumulation_scanner.exchange.okx_public_client import OKXPublicClient
from accumulation_scanner.reporting.daily_report import DailyReportBuilder
from accumulation_scanner.storage.repository import Repository


class ScannerService:
    def __init__(self):
        self.client = OKXPublicClient()
        self.repo = Repository()
        self.filters = MarketFilters()
        self.scorer = AccumulationScorer()

    async def run_scan(self) -> dict:
        tickers = await self.client.get_spot_tickers()
        scanned = 0
        rejected = 0
        saved = 0
        errors: list[str] = []
        for ticker in tickers:
            try:
                candles = await self.client.get_candles(ticker.inst_id, settings.candle_bar, settings.candle_limit)
                reason = self.filters.reject_reason(ticker, candles)
                if reason:
                    self.repo.log_rejection(ticker.inst_id, reason)
                    rejected += 1
                    continue
                previous = self.repo.previous_score(ticker.inst_id)
                first_seen = self.repo.first_active_seen(ticker.inst_id)
                result = self.scorer.score(ticker.inst_id, candles, previous, first_seen)
                signal_id = self.repo.save_score(result, settings.min_accumulation_score)
                scanned += 1
                if signal_id:
                    saved += 1
            except Exception as exc:
                errors.append(f"{ticker.inst_id}: {exc}")
        report = DailyReportBuilder(self.repo).build_and_save()
        return {
            "tickers_seen": len(tickers),
            "scanned": scanned,
            "rejected": rejected,
            "signals_saved": saved,
            "top_candidates": report["top_10_accumulation_candidates"],
            "errors": errors[:20],
        }
