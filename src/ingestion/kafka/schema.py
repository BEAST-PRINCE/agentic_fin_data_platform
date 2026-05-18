"""
Shared article schema helpers for the scraping → Kafka → Bronze pipeline.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from dateutil import parser as date_parser


def generate_article_id(
    url: Optional[str] = None,
    title: Optional[str] = None,
    source: Optional[str] = None,
    content: Optional[str] = None,
) -> str:
    """Deterministic MD5 article_id (url → title+source → content → random)."""
    if url:
        id_input = url
    elif title or source:
        id_input = f"{title or ''}{source or ''}"
    elif content:
        id_input = content
    else:
        id_input = str(uuid.uuid4())
    return hashlib.md5(id_input.encode("utf-8")).hexdigest()


def sanitize_source_partition(source: Optional[str]) -> str:
    """Hive-style partition value for bronze/silver source= paths."""
    if not source or not str(source).strip():
        return "unknown"
    return str(source).strip().lower().replace(" ", "_")


def normalize_published_at(value: Any) -> str:
    """
    Normalize publish timestamps to UTC ISO-8601 with Z suffix for Spark/Gold.
    Falls back to current UTC when parsing fails or value is empty.
    """
    if value is None or str(value).strip() == "":
        dt = datetime.now(timezone.utc)
    else:
        try:
            dt = date_parser.parse(str(value))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
        except (ValueError, TypeError, OverflowError):
            dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"


def build_bronze_s3_key(source: Optional[str], article_id: str, ingested_at: Optional[str] = None) -> str:
    """
    Bronze object key with Hive-style partitions for incremental silver reads.
    raw_news/source={source}/year=YYYY/month=MM/day=DD/{article_id}.json
    """
    partition_source = sanitize_source_partition(source)
    if ingested_at:
        try:
            dt = date_parser.parse(str(ingested_at.replace("Z", "+00:00")))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError, OverflowError):
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)

    return (
        f"raw_news/source={partition_source}/"
        f"year={dt.year}/month={dt.month:02d}/day={dt.day:02d}/"
        f"{article_id}.json"
    )


def build_bronze_kafka_payload(article_data: dict) -> dict:
    """
    Canonical Kafka/bronze document aligned with the silver layer schema.
    """
    article_id = article_data.get("article_id") or generate_article_id(
        url=article_data.get("url"),
        title=article_data.get("title"),
        source=article_data.get("source"),
        content=article_data.get("content"),
    )

    author = article_data.get("author")
    if author is None or str(author).strip() == "":
        author = "unknown"

    description = article_data.get("description") or ""

    tags = article_data.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    ingested_at = article_data.get("ingested_at")
    if not ingested_at:
        ingested_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return {
        "article_id": article_id,
        "title": article_data.get("title", ""),
        "content": article_data.get("content", ""),
        "description": description,
        "source": article_data.get("source", "unknown"),
        "url": article_data.get("url", ""),
        "published_at": normalize_published_at(article_data.get("published_at")),
        "author": author,
        "category": article_data.get("category") or "general",
        "ingested_at": ingested_at,
        "tags": tags,
    }
