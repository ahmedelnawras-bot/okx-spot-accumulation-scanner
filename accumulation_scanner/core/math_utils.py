import math
from statistics import mean, pstdev


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    if math.isnan(value) or math.isinf(value):
        return low
    return max(low, min(high, value))


def pct_change(old: float, new: float) -> float:
    if old == 0:
        return 0.0
    return ((new - old) / old) * 100


def safe_mean(values: list[float]) -> float:
    values = [v for v in values if v is not None]
    return mean(values) if values else 0.0


def safe_std(values: list[float]) -> float:
    values = [v for v in values if v is not None]
    return pstdev(values) if len(values) > 1 else 0.0
