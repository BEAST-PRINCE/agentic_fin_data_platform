import os
import sys
import threading

import duckdb

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.common import config
from src.common.logger import get_logger

logger = get_logger(__name__)


class DuckDBClient:
    """
    DuckDB client for read-only lakehouse queries.

    Each thread gets its own in-memory connection with httpfs configured, so
    concurrent dashboard API requests are not serialized on a global lock.
    """

    def __init__(self):
        self._local = threading.local()
        logger.info("DuckDB client ready (thread-local read connections).")

    def _configure_s3(self, conn: duckdb.DuckDBPyConnection) -> None:
        conn.execute("INSTALL httpfs;")
        conn.execute("LOAD httpfs;")

        secure = str(config.MINIO_SECURE).lower() == "true"
        use_ssl = "true" if secure else "false"

        conn.execute(f"SET s3_endpoint='{config.MINIO_ENDPOINT}'")
        conn.execute(f"SET s3_access_key_id='{config.MINIO_ACCESS_KEY}'")
        conn.execute(f"SET s3_secret_access_key='{config.MINIO_SECRET_KEY}'")
        conn.execute(f"SET s3_use_ssl={use_ssl}")
        conn.execute("SET s3_url_style='path'")

    def _get_read_connection(self) -> duckdb.DuckDBPyConnection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = duckdb.connect(":memory:")
            self._configure_s3(conn)
            self._local.conn = conn
        return conn

    def query(self, sql_query: str):
        """Execute a read query on the current thread's DuckDB connection."""
        conn = self._get_read_connection()
        try:
            result = conn.execute(sql_query)
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            error_msg = str(e)
            if (
                "No files found that match the pattern" not in error_msg
                and "Timeout was reached error" not in error_msg
            ):
                logger.error(f"Failed to execute query: {e}")
            raise

    def get_gold_path(self, table_name: str) -> str:
        """Returns the S3 URI for a Gold table."""
        return f"s3://{config.MINIO_GOLD_BUCKET}/{table_name}/**/*.parquet"


# Singleton instance
db = DuckDBClient()
