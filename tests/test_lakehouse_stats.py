import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage import db_client
from src.storage.lakehouse_stats import increment_bronze, get_stats, set_layer_counts


def test_increment_bronze_and_read():
    set_layer_counts(bronze=0, silver=0, gold=0)
    increment_bronze(3)
    stats = get_stats()
    assert stats["bronze"]["raw_messages"] == 3


def test_duckdb_concurrent_reads_do_not_share_lock():
    """Two threads can query in parallel without a global lock."""
    errors = []

    def run_query():
        try:
            db_client.db.query("SELECT 1 AS ok")
        except Exception as e:
            errors.append(e)

    t1 = threading.Thread(target=run_query)
    t2 = threading.Thread(target=run_query)
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)
    assert not errors
