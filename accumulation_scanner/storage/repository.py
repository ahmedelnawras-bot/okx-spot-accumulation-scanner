from __future__ import annotations

import json
from datetime import datetime, timezone
from accumulation_scanner.core.models import ScoreResult, SignalOutcome
from accumulation_scanner.storage.database import connect


class Repository:
    def latest_signal_for(self, inst_id: str):
        with connect() as conn:
            return conn.execute("SELECT * FROM signals WHERE inst_id=? ORDER BY created_at DESC LIMIT 1", (inst_id,)).fetchone()

    def first_active_seen(self, inst_id: str) -> datetime | None:
        with connect() as conn:
            row = conn.execute("SELECT first_accumulation_seen FROM signals WHERE inst_id=? AND is_active=1 ORDER BY first_accumulation_seen ASC LIMIT 1", (inst_id,)).fetchone()
            return datetime.fromisoformat(row[0]) if row else None

    def previous_score(self, inst_id: str) -> float | None:
        row = self.latest_signal_for(inst_id)
        return float(row["accumulation_score"]) if row else None

    def save_score(self, result: ScoreResult, threshold: float) -> int | None:
        with connect() as conn:
            conn.execute("INSERT INTO score_history(inst_id, created_at, accumulation_score, fresh_accumulation_score, velocity, status) VALUES(?,?,?,?,?,?)",
                         (result.inst_id, result.created_at.isoformat(), result.accumulation_score, result.fresh_accumulation_score, result.accumulation_velocity, result.status))
            if result.accumulation_score < threshold or result.status in ("Distribution Risk", "Failed Accumulation"):
                conn.execute("UPDATE signals SET is_active=0 WHERE inst_id=? AND is_active=1", (result.inst_id,))
                return None
            first_seen = self.first_active_seen(result.inst_id) or result.created_at
            cur = conn.execute("""
                INSERT INTO signals(inst_id, first_accumulation_seen, created_at, accumulation_score, accumulation_age_days,
                accumulation_velocity, fresh_accumulation_score, distribution_score, capital_efficiency_score, status, reasons, is_active)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,1)
            """, (result.inst_id, first_seen.isoformat(), result.created_at.isoformat(), result.accumulation_score,
                  result.accumulation_age_days, result.accumulation_velocity, result.fresh_accumulation_score,
                  result.distribution_score, result.capital_efficiency_score, result.status, json.dumps(result.reasons)))
            return int(cur.lastrowid)

    def log_rejection(self, inst_id: str, reason: str):
        with connect() as conn:
            conn.execute("INSERT INTO scan_rejections(inst_id, created_at, reason) VALUES(?,?,?)",
                         (inst_id, datetime.now(timezone.utc).isoformat(), reason))

    def top_candidates(self, limit: int = 10):
        with connect() as conn:
            return [dict(r) for r in conn.execute("""
                SELECT * FROM signals WHERE is_active=1
                ORDER BY fresh_accumulation_score DESC, accumulation_velocity DESC, accumulation_age_days ASC LIMIT ?
            """, (limit,)).fetchall()]

    def active_signals(self):
        with connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM signals WHERE is_active=1 ORDER BY created_at DESC").fetchall()]

    def pending_outcome_signals(self):
        with connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM signals").fetchall()]

    def save_outcome(self, inst_id: str, outcome: SignalOutcome):
        with connect() as conn:
            conn.execute("""
            INSERT OR IGNORE INTO outcomes(signal_id, inst_id, horizon_days, evaluated_at, future_return_pct, max_gain_pct, max_drawdown_pct, verdict)
            VALUES(?,?,?,?,?,?,?,?)
            """, (outcome.signal_id, inst_id, outcome.horizon_days, outcome.evaluated_at.isoformat(), outcome.future_return_pct,
                  outcome.max_gain_pct, outcome.max_drawdown_pct, outcome.verdict))

    def save_daily_report(self, report_date: str, payload: dict):
        with connect() as conn:
            conn.execute("INSERT OR REPLACE INTO daily_reports(report_date, created_at, payload) VALUES(?,?,?)",
                         (report_date, datetime.now(timezone.utc).isoformat(), json.dumps(payload, ensure_ascii=False)))

    def latest_daily_report(self):
        with connect() as conn:
            row = conn.execute("SELECT * FROM daily_reports ORDER BY report_date DESC LIMIT 1").fetchone()
            return dict(row) if row else None
