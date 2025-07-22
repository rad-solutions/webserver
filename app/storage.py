import logging
import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage

logger = logging.getLogger(__name__)


class MockStorage(FileSystemStorage):
    def __init__(self):
        location = os.path.join(settings.MEDIA_ROOT, "mock_s3")
        super().__init__(location=location)

    def url(self, name):
        logger.info(f"[MOCK] Generando URL para: {name}")
        return f"{settings.MEDIA_URL.rstrip('/')}/mock_s3/{name}"

    def _save(self, name, content):
        logger.info(f"[MOCK] Guardando archivo: {name}")
        return super()._save(name, content)


class PDFStorage(S3Boto3Storage):
    location = "media/"

    def __new__(cls, *args, **kwargs):
        use_mock = os.getenv("USE_MOCK_STORAGE", "False").lower() == "true"
        if use_mock:
            logger.info("USE_MOCK_STORAGE is True. Using MockStorage.")
            return MockStorage()

        logger.info("USE_MOCK_STORAGE is False. Using S3Boto3Storage (PDFStorage).")
        return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("PDFStorage (S3Boto3Storage) initialized.")
        logger.info(f"Bucket Name: {self.bucket_name}")
        logger.info(f"Location: {self.location}")

    def _save(self, name, content):
        logger.info(f"Attempting to save '{name}' to S3 bucket '{self.bucket_name}'.")
        try:
            # The content object needs to be reset before saving
            content.seek(0)
            saved_name = super()._save(name, content)
            logger.info(f"Successfully saved '{name}' as '{saved_name}' in S3.")
            return saved_name
        except Exception as e:
            # Log the full exception traceback
            logger.error(f"Failed to save '{name}' to S3. Error: {e}", exc_info=True)
            raise
