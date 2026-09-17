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


def delete_original(source_path: str | None) -> None:
    """Delete an uploaded original from S3 when the material uses S3 storage."""
    if not source_path or not source_path.startswith("s3://"):
        return

    location = source_path[len("s3://"):]
    bucket, separator, key = location.partition("/")
    if not separator or not bucket or not key:
        raise ValueError("Invalid S3 material source path")

    import boto3

    boto3.client("s3", region_name=config.AWS_REGION).delete_object(
        Bucket=bucket,
        Key=key,
    )
