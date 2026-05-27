import os
import sys
import duckdb

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.common import config
from src.common.logger import get_logger

logger = get_logger(__name__)

class DuckDBClient:
    def __init__(self):
        self.conn = duckdb.connect(':memory:')
        self._setup_s3()

    def _setup_s3(self):
        """Configure DuckDB to talk to the local MinIO instance"""
        logger.info("Setting up DuckDB S3 extensions for MinIO...")
        self.conn.execute("INSTALL httpfs;")
        self.conn.execute("LOAD httpfs;")
        
        # Determine protocol (http vs https)
        secure = str(config.MINIO_SECURE).lower() == 'true'
        use_ssl = 'true' if secure else 'false'
        
        # Configure the S3 environment
        self.conn.execute(f"SET s3_endpoint='{config.MINIO_ENDPOINT}'")
        self.conn.execute(f"SET s3_access_key_id='{config.MINIO_ACCESS_KEY}'")
        self.conn.execute(f"SET s3_secret_access_key='{config.MINIO_SECRET_KEY}'")
        self.conn.execute(f"SET s3_use_ssl={use_ssl}")
        self.conn.execute("SET s3_url_style='path'")

    def query(self, sql_query: str):
        """Execute a query and return results as a list of dictionaries"""
        try:
            result = self.conn.execute(sql_query)
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            error_msg = str(e)
            if "No files found that match the pattern" not in error_msg and "Timeout was reached error" not in error_msg:
                logger.error(f"Failed to execute query: {e}")
            raise

    def get_gold_path(self, table_name: str) -> str:
        """Returns the S3 URI for a Gold table"""
        return f"s3://{config.MINIO_GOLD_BUCKET}/{table_name}/**/*.parquet"

# Singleton instance
db = DuckDBClient()
