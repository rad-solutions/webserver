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
            logger.info("Usando almacenamiento MOCK en lugar de S3")
            return MockStorage()
        return super().__new__(cls)
