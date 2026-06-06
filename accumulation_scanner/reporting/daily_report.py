from __future__ import annotations

from datetime import datetime, timezone
from accumulation_scanner.storage.repository import Repository


class DailyReportBuilder:
    def __init__(self, repo: Repository):
        self.repo = repo

    def build_and_save(self) -> dict:
        candidates = self.repo.top_candidates(10)
        active = self.repo.active_signals()
        failed = [s for s in active if s["status"] == "Failed Accumulation"]
        distribution = [s for s in active if s["status"] == "Distribution Risk"]
        payload = {
            "report_date": datetime.now(timezone.utc).date().isoformat(),
            "market_snapshot": {
                "active_signals": len(active),
                "top_candidate_count": len(candidates),
            },
            "top_10_accumulation_candidates": candidates,
            "watchlist": [s for s in active if s["status"] in ("Very Fresh Accumulation", "Early Accumulation", "Confirmed Accumulation")],
            "failed_accumulations": failed,
            "distribution_risks": distribution,
            "lessons_today": self._lessons(candidates),
        }
        self.repo.save_daily_report(payload["report_date"], payload)
        return payload

    def _lessons(self, candidates: list[dict]) -> list[str]:
        if not candidates:
            return ["No valid fresh accumulation candidates. Returning no candidates is valid behavior."]
        top = candidates[0]
        return [
            f"Best fresh profile: {top['inst_id']} with fresh score {top['fresh_accumulation_score']}.",
            "Wait for trigger confirmation before any future spot accumulation decision.",
        ]
