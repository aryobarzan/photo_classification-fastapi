import boto3
from botocore.config import Config
from os import getenv


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=getenv("STORAGE_ENDPOINT"),
        aws_access_key_id=getenv("STORAGE_ACCESS_KEY"),
        aws_secret_access_key=getenv("STORAGE_SECRET_KEY"),
        # Use path-style addressing for S3-compatible storage
        config=Config(s3={"addressing_style": "path"}),
    )


def upload_profile_picture(file_bytes: bytes, filename: str) -> str:
    s3 = get_s3_client()

    bucket = getenv("STORAGE_BUCKET_PROFILE_PICTURES") or "profile-pictures"
    s3.put_object(Bucket=bucket, Key=filename, Body=file_bytes)
    return f"{getenv('STORAGE_ENDPOINT')}/{bucket}/{filename}"
