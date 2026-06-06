from __future__ import annotations

from datetime import datetime, timezone
from accumulation_scanner.core.math_utils import clamp, pct_change, safe_mean, safe_std
from accumulation_scanner.core.models import Candle, ScoreResult


class AccumulationScorer:
    """Scores fresh pre-breakout accumulation. Penalizes pumps and distribution."""

    def score(self, inst_id: str, candles: list[Candle], previous_score: float | None = None, first_seen: datetime | None = None) -> ScoreResult:
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        vols = [c.volume_ccy for c in candles]
        recent = candles[-14:]
        base = candles[-60:-14] if len(candles) >= 74 else candles[:-14]

        recent_vol = safe_mean([c.volume_ccy for c in recent])
        base_vol = safe_mean([c.volume_ccy for c in base]) or recent_vol
        volume_ratio = recent_vol / base_vol if base_vol else 1
        volume_accumulation = clamp((volume_ratio - 0.8) * 70)

        recent_return = abs(pct_change(recent[0].close, recent[-1].close)) if len(recent) > 1 else 0
        recent_range_pct = ((max(c.high for c in recent) - min(c.low for c in recent)) / recent[-1].close) * 100
        price_stability = clamp(100 - (recent_return * 3.0) - (recent_range_pct * 2.0))

        old_close = closes[-31] if len(closes) > 31 else closes[0]
        strength_30d = pct_change(old_close, closes[-1])
        recent_7d = pct_change(closes[-8], closes[-1]) if len(closes) > 8 else 0
        relative_strength = clamp(50 + strength_30d * 1.5 + recent_7d)

        down_days = [c for c in recent if c.close < c.open]
        absorption_hits = 0
        for c in down_days:
            lower_wick = min(c.open, c.close) - c.low
            total_range = max(c.high - c.low, 1e-12)
            if lower_wick / total_range > 0.35 and c.volume_ccy >= recent_vol:
                absorption_hits += 1
        dip_absorption = clamp((absorption_hits / max(len(down_days), 1)) * 100)

        higher_lows = sum(1 for i in range(1, len(lows[-20:])) if lows[-20:][i] >= lows[-20:][i - 1] * 0.985)
        not_breaking_down = closes[-1] >= min(lows[-30:]) * 1.08 if len(lows) >= 30 else True
        structure_health = clamp((higher_lows / 19) * 70 + (30 if not_breaking_down else 0))

        raw_score = (
            volume_accumulation * 0.25
            + price_stability * 0.25
            + relative_strength * 0.15
            + dip_absorption * 0.20
            + structure_health * 0.15
        )

        distribution_score = self._distribution_score(candles)
        accumulation_score = clamp(raw_score - distribution_score * 0.35)

        if previous_score is None:
            velocity = 0.0
        else:
            velocity = clamp((accumulation_score - previous_score) * 10, -100, 100)

        now = datetime.now(timezone.utc)
        age = 0 if first_seen is None else max(0, (now - first_seen).days)
        freshness_bonus = 18 if age <= 7 else 10 if age <= 14 else 4 if age <= 30 else 0
        age_penalty = max(0, age - 21) * 0.45
        velocity_component = max(-18, min(18, velocity * 0.35))
        fresh_score = clamp(accumulation_score + freshness_bonus + velocity_component - age_penalty - distribution_score * 0.15)

        capital_efficiency_score = clamp(fresh_score - max(0, age - 30) * 0.8)
        status = self._status(accumulation_score, fresh_score, velocity, age, distribution_score)
        reasons = self._reasons(volume_accumulation, price_stability, dip_absorption, structure_health, velocity, distribution_score)

        return ScoreResult(
            inst_id=inst_id,
            accumulation_score=round(accumulation_score, 2),
            volume_accumulation=round(volume_accumulation, 2),
            price_stability=round(price_stability, 2),
            relative_strength=round(relative_strength, 2),
            dip_absorption=round(dip_absorption, 2),
            structure_health=round(structure_health, 2),
            accumulation_velocity=round(velocity, 2),
            accumulation_age_days=age,
            fresh_accumulation_score=round(fresh_score, 2),
            distribution_score=round(distribution_score, 2),
            capital_efficiency_score=round(capital_efficiency_score, 2),
            status=status,
            reasons=reasons,
            created_at=now,
        )

    def _distribution_score(self, candles: list[Candle]) -> float:
        recent = candles[-14:]
        avg_vol = safe_mean([c.volume_ccy for c in recent])
        red_high_volume = sum(1 for c in recent if c.close < c.open and c.volume_ccy > avg_vol * 1.25)
        lower_highs = sum(1 for i in range(1, len(recent)) if recent[i].high < recent[i - 1].high)
        volatility = safe_std([pct_change(c.open, c.close) for c in recent])
        return clamp(red_high_volume * 18 + lower_highs * 3 + volatility * 4)

    def _status(self, score: float, fresh: float, velocity: float, age: int, distribution: float) -> str:
        if distribution >= 65:
            return "Distribution Risk"
        if score < 55:
            return "Failed Accumulation"
        if velocity < -20:
            return "Weakening Accumulation"
        if age <= 7 and fresh >= 75:
            return "Very Fresh Accumulation"
        if age <= 21:
            return "Early Accumulation"
        if age <= 45 and score >= 70:
            return "Confirmed Accumulation"
        return "Mature Accumulation"

    def _reasons(self, volume: float, stability: float, absorption: float, structure: float, velocity: float, distribution: float) -> list[str]:
        reasons = []
        if volume >= 65: reasons.append("volume expanding without pump")
        if stability >= 70: reasons.append("price remains stable")
        if absorption >= 55: reasons.append("dips are being absorbed")
        if structure >= 65: reasons.append("structure remains healthy")
        if velocity > 10: reasons.append("accumulation is strengthening")
        if distribution > 50: reasons.append("distribution risk detected")
        return reasons or ["mixed but acceptable accumulation profile"]
