import os
import shutil
import logging
from typing import Optional

logger = logging.getLogger("verimeter.backend.storage")

class ObjectStorageClient:
    def __init__(self):
        self.use_s3 = False
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "verimeter-storage")
        
        # Check AWS credentials
        self.aws_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        if self.aws_key and self.aws_secret:
            try:
                import boto3
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=self.aws_key,
                    aws_secret_access_key=self.aws_secret
                )
                self.use_s3 = True
                logger.info("S3 Object Storage initialized successfully.")
            except ImportError:
                logger.warning("boto3 package not installed. Falling back to local storage.")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}. Falling back to local storage.")
                
        if not self.use_s3:
            # Setup local fallback storage folder inside workspace results directory
            self.local_storage_dir = os.path.join("results", "storage")
            os.makedirs(self.local_storage_dir, exist_ok=True)
            logger.info(f"Local Fallback Object Storage initialized: {self.local_storage_dir}")
            
    def upload_file(self, local_filepath: str, object_name: Optional[str] = None) -> str:
        """
        Uploads a file to S3 bucket or copies it to the local fallback storage directory.
        Returns the reference path or S3 URL.
        """
        if not os.path.exists(local_filepath):
            raise FileNotFoundError(f"File not found: {local_filepath}")
            
        filename = os.path.basename(local_filepath)
        obj_name = object_name or filename
        
        if self.use_s3:
            try:
                self.s3_client.upload_file(local_filepath, self.bucket_name, obj_name)
                s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{obj_name}"
                logger.info(f"Uploaded {local_filepath} to S3: {s3_url}")
                return s3_url
            except Exception as e:
                logger.error(f"S3 upload failed: {e}. Attempting local copy.")
                
        # Local copy fallback
        dest_path = os.path.join(self.local_storage_dir, obj_name)
        # Ensure target subdirectory exists (in case of nested paths)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(local_filepath, dest_path)
        logger.info(f"Copied file to local storage: {dest_path}")
        return dest_path

storage_client = ObjectStorageClient()
