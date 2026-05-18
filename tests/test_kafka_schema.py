import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingestion.kafka.schema import (
    build_bronze_kafka_payload,
    build_bronze_s3_key,
    generate_article_id,
    normalize_published_at,
    sanitize_source_partition,
)


def test_generate_article_id_from_url():
    a = generate_article_id(url="https://example.com/a")
    b = generate_article_id(url="https://example.com/a")
    assert a == b


def test_normalize_published_at_iso():
    result = normalize_published_at("2024-05-12T10:00:00Z")
    assert result.startswith("2024-05-12T10:00:00")


def test_normalize_published_at_human_readable():
    result = normalize_published_at("May 12, 2024 10:30 AM")
    assert "2024" in result and result.endswith("Z")


def test_sanitize_source_partition():
    assert sanitize_source_partition("Financial Express") == "financial_express"


def test_bronze_s3_key_uses_source_partition():
    key = build_bronze_s3_key("LiveMint", "abc123", "2024-05-12T10:00:00Z")
    assert key.startswith("raw_news/source=livemint/")
    assert key.endswith("abc123.json")


def test_bronze_payload_normalizes_date_and_author():
    payload = build_bronze_kafka_payload(
        {
            "url": "https://example.com/x",
            "title": "T",
            "content": "body",
            "source": "LiveMint",
            "published_at": "May 1, 2024",
        }
    )
    assert payload["published_at"].endswith("Z")
    assert payload["author"] == "unknown"
    assert "image_url" not in payload
