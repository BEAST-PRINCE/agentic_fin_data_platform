"""
Maintained lakehouse record counters stored in MinIO (system-logs/lakehouse_stats.json).

Updated incrementally by the bronze consumer and pipeline jobs; read by the dashboard API.
Avoids expensive bronze list_objects and full-table DuckDB COUNT queries for throughput stats.
"""

from __future__ import annotations

import io
import json
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.common import config
from src.common.logger import get_logger
from src.storage.minio_client import MinIOClient

logger = get_logger(__name__)

STATS_BUCKET = "system-logs"
STATS_KEY = "lakehouse_stats.json"

_write_lock = threading.Lock()


def _empty_stats() -> Dict[str, Any]:
    return {
        "bronze": {"raw_messages": 0},
        "silver": {"cleaned_articles": 0},
        "gold": {"serving_articles": 0},
        "updated_at": None,
    }


def _ensure_bucket(client: MinIOClient) -> None:
    client.ensure_bucket_exists(STATS_BUCKET)


def _read_stats_unlocked(client: MinIOClient) -> Dict[str, Any]:
    _ensure_bucket(client)
    try:
        response = client.client.get_object(STATS_BUCKET, STATS_KEY)
        try:
            data = json.loads(response.read().decode("utf-8"))
        finally:
            response.close()
            response.release_conn()
        stats = _empty_stats()
        stats["bronze"]["raw_messages"] = int(data.get("bronze", {}).get("raw_messages", 0))
        stats["silver"]["cleaned_articles"] = int(data.get("silver", {}).get("cleaned_articles", 0))
        stats["gold"]["serving_articles"] = int(data.get("gold", {}).get("serving_articles", 0))
        stats["updated_at"] = data.get("updated_at")
        return stats
    except Exception:
        return _empty_stats()


def _write_stats_unlocked(client: MinIOClient, stats: Dict[str, Any]) -> None:
    _ensure_bucket(client)
    stats = {
        "bronze": {"raw_messages": int(stats["bronze"]["raw_messages"])},
        "silver": {"cleaned_articles": int(stats["silver"]["cleaned_articles"])},
        "gold": {"serving_articles": int(stats["gold"]["serving_articles"])},
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    payload = json.dumps(stats, indent=2).encode("utf-8")
    client.client.put_object(
        STATS_BUCKET,
        STATS_KEY,
        data=io.BytesIO(payload),
        length=len(payload),
        content_type="application/json",
    )


def get_stats() -> Dict[str, Any]:
    """Read maintained counters (single MinIO GET)."""
    client = MinIOClient()
    with _write_lock:
        return _read_stats_unlocked(client)


def increment_bronze(delta: int = 1) -> Dict[str, Any]:
    """Increment bronze raw message count by delta (e.g. after each successful ingest)."""
    if delta <= 0:
        return get_stats()
    client = MinIOClient()
    with _write_lock:
        stats = _read_stats_unlocked(client)
        stats["bronze"]["raw_messages"] += delta
        _write_stats_unlocked(client, stats)
        return stats


def add_silver_records(delta: int) -> Dict[str, Any]:
    """Add newly written silver records after a successful silver job."""
    if delta <= 0:
        return get_stats()
    client = MinIOClient()
    with _write_lock:
        stats = _read_stats_unlocked(client)
        stats["silver"]["cleaned_articles"] += delta
        _write_stats_unlocked(client, stats)
        return stats


def add_gold_records(delta: int) -> Dict[str, Any]:
    """Add newly written gold serving articles after a successful gold job."""
    if delta <= 0:
        return get_stats()
    client = MinIOClient()
    with _write_lock:
        stats = _read_stats_unlocked(client)
        stats["gold"]["serving_articles"] += delta
        _write_stats_unlocked(client, stats)
        return stats


def set_layer_counts(
    bronze: Optional[int] = None,
    silver: Optional[int] = None,
    gold: Optional[int] = None,
) -> Dict[str, Any]:
    """Overwrite layer totals (for one-time backfill or reconciliation)."""
    client = MinIOClient()
    with _write_lock:
        stats = _read_stats_unlocked(client)
        if bronze is not None:
            stats["bronze"]["raw_messages"] = bronze
        if silver is not None:
            stats["silver"]["cleaned_articles"] = silver
        if gold is not None:
            stats["gold"]["serving_articles"] = gold
        _write_stats_unlocked(client, stats)
        return stats
