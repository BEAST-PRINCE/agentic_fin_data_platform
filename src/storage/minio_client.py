import io
from minio import Minio
from minio.error import S3Error
from src.common import config
from src.common.logger import get_logger

logger = get_logger(__name__)

class MinIOClient:
    def __init__(self):
        # minio client expects endpoint without http:// or https://
        endpoint = config.MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
        
        self.client = Minio(
            endpoint,
            access_key=config.MINIO_ACCESS_KEY,
            secret_key=config.MINIO_SECRET_KEY,
            secure=config.MINIO_SECURE
        )
        logger.info(f"Initialized MinIO client at {endpoint}")

    def ensure_bucket_exists(self, bucket_name: str):
        """Creates the bucket if it does not already exist."""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created bucket '{bucket_name}' in MinIO.")
            else:
                logger.info(f"Bucket '{bucket_name}' already exists.")
        except S3Error as e:
            logger.error(f"Error checking/creating bucket '{bucket_name}': {e}")
            raise

    def upload_stream(self, bucket_name: str, object_name: str, data: io.BytesIO, length: int):
        """Uploads an in-memory byte stream to a specified bucket and path."""
        try:
            data.seek(0) # Ensure we're reading from the beginning of the stream
            self.client.put_object(
                bucket_name,
                object_name,
                data=data,
                length=length,
                content_type="application/jsonl"
            )
            logger.info(f"Successfully uploaded {length} bytes to '{bucket_name}/{object_name}'")
        except S3Error as e:
            logger.error(f"Error uploading to MinIO: {e}")
            raise
