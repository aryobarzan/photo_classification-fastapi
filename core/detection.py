# This file contains the logic for scanning a given image for NSFW content, as well as for classifying the image.
# These operations are delegated to the classification microservice.

import httpx
from os import getenv

CLASSIFICATION_SERVICE_URL = getenv(
    "CLASSIFICATION_SERVICE_URL", "http://classification-service:8001"
)


async def detect_nsfw_content(image_bytes: bytes, content_type: str) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CLASSIFICATION_SERVICE_URL}/detect-nsfw",
            files={"file": ("image", image_bytes, content_type)},
        )
        response.raise_for_status()
        return response.json()["nsfw"]


async def classify_image(image_bytes: bytes, content_type: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CLASSIFICATION_SERVICE_URL}/classify",
            files={"file": ("image", image_bytes, content_type)},
        )
        response.raise_for_status()
        return response.json()["label"]
