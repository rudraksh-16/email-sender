"""Bulk-send campaigns: queue jobs, watch progress, retry failed rows.

Planned endpoints:
    GET    /                       list
    POST   /                       create + enqueue
    POST   /from-csv               create from uploaded CSV
    GET    /{id}                   read with progress counters
    POST   /{id}/cancel
    GET    /{id}/logs              per-row send logs
    POST   /logs/{log_id}/retry    retry a single failed row

The orchestrator lives in ``app.services.campaign_runner`` — this router only
validates input, persists the campaign row, and schedules the BackgroundTask.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()
