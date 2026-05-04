from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, HTTPException
from transformers import Pipeline, pipeline
from PIL import Image
import io

# We hold the loaded models in memory to avoid having to reload them for every request.
models: dict[str, Pipeline] = {}


# Taken from: https://fastapi.tiangolo.com/advanced/events/#lifespan
@asynccontextmanager
async def lifespan(_: FastAPI):
    # During startup, load the NSFW detection and classification models into memory.
    # We want the models to be loaded before our FastAPI server starts accepting requests.
    models["nsfw"] = pipeline(
        "image-classification", model="Falconsai/nsfw_image_detection"
    )
    models["classify"] = pipeline(
        "image-classification", model="google/vit-base-patch16-224"
    )
    yield
    # During shutdown, clear the models from memory.
    models.clear()


# Initialize the FastAPI app with the lifespan function, which will load the models during startup and clear them during shutdown.
app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


ALLOWED_PROFILE_PICTURE_TYPES = ["image/jpeg", "image/png"]
MAX_PROFILE_PICTURE_SIZE = 5 * 1024 * 1024  # 5 MB


# Check if the uploaded file is a supported image type and whether its size does not exceed the maximum allowed size.
# If the file is valid, return its bytes. Otherwise, raise an HTTPException.
async def validate_image_file(file: UploadFile) -> bytes:
    if not file.content_type or file.content_type not in ALLOWED_PROFILE_PICTURE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"File must be an image of any of the following types: {', '.join(ALLOWED_PROFILE_PICTURE_TYPES)}.",
        )

    image_bytes = await file.read()
    if len(image_bytes) > MAX_PROFILE_PICTURE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds the maximum allowed size of {MAX_PROFILE_PICTURE_SIZE} bytes.",
        )
    return image_bytes


@app.post("/classify")
async def classify(file: UploadFile):
    image_bytes = await validate_image_file(file)

    image = Image.open(io.BytesIO(image_bytes))
    results = models["classify"](image)
    return {"label": results[0]["label"] if results else "Unknown"}


@app.post("/detect-nsfw")
async def detect_nsfw(file: UploadFile):
    image_bytes = await validate_image_file(file)

    image = Image.open(io.BytesIO(image_bytes))
    results = models["nsfw"](image)
    is_nsfw = any(r["label"] == "NSFW" and r["score"] > 0.5 for r in results)
    return {"nsfw": is_nsfw}
