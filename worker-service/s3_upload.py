import os
import logging

logger = logging.getLogger(__name__)

AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
LOCAL_SCREENSHOT_DIR = "/app/screenshots"


async def upload_screenshot(image_bytes: bytes, filename: str) -> str:
    """
    Upload a screenshot to S3 and return the public URL.
    If AWS is not configured, save locally and return a placeholder URL.
    """
    if AWS_BUCKET_NAME:
        try:
            import boto3
            s3 = boto3.client("s3", region_name=AWS_REGION)
            key = f"screenshots/{filename}"
            s3.put_object(
                Bucket=AWS_BUCKET_NAME,
                Key=key,
                Body=image_bytes,
                ContentType="image/png",
                ACL="public-read",
            )
            url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"
            logger.info(f"Uploaded screenshot to S3: {url}")
            return url
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")

    # Fallback: save locally
    try:
        os.makedirs(LOCAL_SCREENSHOT_DIR, exist_ok=True)
        filepath = os.path.join(LOCAL_SCREENSHOT_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        logger.info(f"Saved screenshot locally: {filepath}")
        return f"/screenshots/{filename}"
    except Exception as e:
        logger.error(f"Local save failed: {e}")
        return ""
