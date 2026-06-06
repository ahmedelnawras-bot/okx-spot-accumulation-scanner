from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Ticker:
    inst_id: str
    last: float
    bid: float
    ask: float
    volume_24h_ccy: float
    volume_24h_base: float

    @property
    def spread_pct(self) -> float:
        if self.bid <= 0 or self.ask <= 0:
            return 999.0
        mid = (self.bid + self.ask) / 2
        return ((self.ask - self.bid) / mid) * 100


@dataclass(frozen=True)
class Candle:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    volume_ccy: float


@dataclass(frozen=True)
class ScoreResult:
    inst_id: str
    accumulation_score: float
    volume_accumulation: float
    price_stability: float
    relative_strength: float
    dip_absorption: float
    structure_health: float
    accumulation_velocity: float
    accumulation_age_days: int
    fresh_accumulation_score: float
    distribution_score: float
    capital_efficiency_score: float
    status: str
    reasons: list[str]
    created_at: datetime


@dataclass(frozen=True)
class SignalOutcome:
    signal_id: int
    horizon_days: int
    future_return_pct: float
    max_gain_pct: float
    max_drawdown_pct: float
    verdict: str
    evaluated_at: datetime
