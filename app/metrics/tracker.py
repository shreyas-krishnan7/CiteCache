
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

from app.config import settings


def log_event(
    query: str,
    source: str,               # "cache" or "generated"
    confidence: float | None,
    latency_ms: float | None,
    cached_this_run: bool | None,  # True/False if source=="generated" (write attempted), None if source=="cache"
) -> None:
    path = Path(settings.metrics_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "source": source,
        "confidence": confidence,
        "latency_ms": latency_ms,
        "cached_this_run": cached_this_run,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _read_records(path: str | None = None) -> list[dict]:
    p = Path(path or settings.metrics_log_path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def summarize(path: str | None = None) -> dict:
    records = _read_records(path)
    total = len(records)
    if total == 0:
        return {"total_queries": 0}

    hits = [r for r in records if r["source"] == "cache"]
    misses = [r for r in records if r["source"] == "generated"]

    hit_latencies = [r["latency_ms"] for r in hits if r["latency_ms"] is not None]
    miss_latencies = [r["latency_ms"] for r in misses if r["latency_ms"] is not None]
    avg_latency_hit = sum(hit_latencies) / len(hit_latencies) if hit_latencies else None
    avg_latency_miss = sum(miss_latencies) / len(miss_latencies) if miss_latencies else None

    latency_reduction_pct = None
    if avg_latency_hit is not None and avg_latency_miss:
        latency_reduction_pct = (1 - avg_latency_hit / avg_latency_miss) * 100

    writes = sum(1 for r in misses if r.get("cached_this_run") is True)
    write_rejections = sum(1 for r in misses if r.get("cached_this_run") is False)

    confidences = [r["confidence"] for r in records if r.get("confidence") is not None]
    avg_confidence = sum(confidences) / len(confidences) if confidences else None

    return {
        "total_queries": total,
        "cache_hits": len(hits),
        "cache_misses": len(misses),
        "cache_hit_rate": len(hits) / total,
        "avg_latency_hit_ms": avg_latency_hit,
        "avg_latency_miss_ms": avg_latency_miss,
        "latency_reduction_pct": latency_reduction_pct,
        "cache_writes": writes,
        "cache_write_rejections_low_confidence": write_rejections,
        "avg_confidence": avg_confidence,
    }


def clear_log(path: str | None = None) -> None:
    p = Path(path or settings.metrics_log_path)
    if p.exists():
        p.unlink()
