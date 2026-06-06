from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from accumulation_scanner.config import settings
from accumulation_scanner.core.scanner import ScannerService
from accumulation_scanner.exchange.okx_public_client import OKXPublicClient
from accumulation_scanner.reporting.daily_report import DailyReportBuilder
from accumulation_scanner.storage.database import init_db
from accumulation_scanner.storage.repository import Repository
from accumulation_scanner.tracking.outcome_tracker import OutcomeTracker

app = FastAPI(title=settings.app_name, version="0.1.0")
scheduler = AsyncIOScheduler()
repo = Repository()


@app.on_event("startup")
async def startup():
    init_db()
    scheduler.add_job(_scheduled_scan, "interval", minutes=settings.scan_interval_minutes, id="scan", replace_existing=True)
    scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown(wait=False)


async def _scheduled_scan():
    await ScannerService().run_scan()


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "mode": "intelligence_only_no_execution"}


@app.post("/scan/run")
async def run_scan():
    return await ScannerService().run_scan()


@app.get("/candidates/top")
def top_candidates(limit: int = 10):
    return {"items": repo.top_candidates(limit)}


@app.get("/watchlist")
def watchlist():
    return {"items": repo.active_signals()}


@app.post("/outcomes/evaluate")
async def evaluate_outcomes():
    tracker = OutcomeTracker(repo, OKXPublicClient())
    return await tracker.evaluate_due_outcomes()


@app.post("/reports/daily/build")
def build_report():
    return DailyReportBuilder(repo).build_and_save()


@app.get("/reports/daily/latest")
def latest_report():
    return repo.latest_daily_report() or {"message": "No report yet. Run /scan/run first."}
