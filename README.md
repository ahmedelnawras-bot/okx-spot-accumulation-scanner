# OKX Spot Accumulation Scanner

Accumulation Intelligence System for OKX Spot markets.

This is **not a trading bot**. It discovers, ranks, tracks, and validates early accumulation signals before breakout.

## MVP Features

- Scans OKX Spot instruments using public OKX API only.
- Filters weak liquidity, wide spread, and recent pumps.
- Computes:
  - Accumulation Score
  - Accumulation Age
  - Accumulation Velocity
  - Fresh Accumulation Score
  - Distribution Score
  - Capital Efficiency Score
- Tracks every signal outcome after 7, 14, 30, and 60 days.
- Stores signals, score history, outcomes, and daily reports in SQLite.
- Exposes FastAPI endpoints for Railway/GitHub deployment.

## Run locally

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn accumulation_scanner.api.app:app --host 0.0.0.0 --port 8000
```

## Main endpoints

- `GET /health`
- `POST /scan/run`
- `GET /candidates/top?limit=10`
- `GET /watchlist`
- `POST /outcomes/evaluate`
- `GET /reports/daily/latest`

## Railway

Use `Procfile`:

```bash
web: uvicorn accumulation_scanner.api.app:app --host 0.0.0.0 --port ${PORT:-8000}
```

## Important

MVP goal: answer whether fresh accumulation signals historically lead to future appreciation. Execution is intentionally excluded.
