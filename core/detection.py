# This file contains the logic for scanning a given image for NSFW content, as well as for classifying the image.

from PIL import Image
from transformers import Pipeline, pipeline


def detect_nsfw_content(image: Image.Image) -> bool:
    nsfw_pipeline: Pipeline = pipeline(
        "image-classification", model="Falconsai/nsfw_image_detection"
    )

    results = nsfw_pipeline(image)

    for result in results:
        if result["label"] == "NSFW" and result["score"] > 0.5:
            return True

    return False


def classify_image(image: Image.Image) -> str:
    classification_pipeline: Pipeline = pipeline(
        "image-classification", model="google/vit-base-patch16-224"
    )

    results = classification_pipeline(image)

    if results:
        return results[0]["label"]

    return "Unknown"
