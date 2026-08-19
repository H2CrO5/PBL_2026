"""Optional S3 storage for original teacher uploads."""

from pathlib import Path
from uuid import uuid4

import config


def store_original(filename: str, content: bytes, course_key: str) -> str:
    """Store in S3 when configured; otherwise retain the safe original filename."""
    safe_name = Path(filename).name or "material"
    if not config.MATERIALS_S3_BUCKET:
        return safe_name
    import boto3

    key = f"{config.MATERIALS_S3_PREFIX}/{course_key}/{uuid4().hex}-{safe_name}"
    boto3.client("s3", region_name=config.AWS_REGION).put_object(
        Bucket=config.MATERIALS_S3_BUCKET,
        Key=key,
        Body=content,
    )
    return f"s3://{config.MATERIALS_S3_BUCKET}/{key}"
