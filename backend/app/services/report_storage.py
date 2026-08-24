from __future__ import annotations

import os
from io import BytesIO
from uuid import uuid4

from minio import Minio


class ReportStorage:
    def __init__(self) -> None:
        self.bucket = os.getenv("MINIO_REPORT_BUCKET", "executive-reports")
        self.client = Minio(
            os.getenv("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "cat_ci"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "cat_ci_demo_password"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
        )

    def store_pdf(self, content: bytes, *, file_name: str, metadata: dict[str, str]) -> str:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
        report_id = uuid4().hex
        self.client.put_object(
            self.bucket,
            f"reports/{report_id}.pdf",
            BytesIO(content),
            length=len(content),
            content_type="application/pdf",
            metadata={"file-name": file_name, **metadata},
        )
        return report_id

    def get_pdf(self, report_id: str) -> tuple[bytes, str]:
        if len(report_id) != 32 or any(character not in "0123456789abcdef" for character in report_id.lower()):
            raise ValueError("Invalid report id")
        object_name = f"reports/{report_id.lower()}.pdf"
        response = self.client.get_object(self.bucket, object_name)
        try:
            content = response.read()
            metadata = self.client.stat_object(self.bucket, object_name).metadata
            return content, metadata.get("x-amz-meta-file-name", "executive-report.pdf")
        finally:
            response.close()
            response.release_conn()


report_storage = ReportStorage()
