from dataclasses import dataclass
from typing import Annotated

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    BackgroundTasks,
)
from fastapi.security import OAuth2PasswordRequestForm
from schemas.user import UserCreateSchema, UserReadSchema, UserRegisterLoginSchema
from schemas.userProfile import UserProfileCreateSchema, UserProfileReadSchema
from database.session import get_db, SessionLocal
from sqlalchemy.orm import Session
import crud.user as crud_user
import crud.userProfile as crud_user_profile
from core.security import create_access_token, verify_password
from core.dependencies import get_current_user
from models.user import User
from core.detection import detect_nsfw_content, classify_image
from core.storage import upload_profile_picture, delete_profile_picture

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserRegisterLoginSchema, status_code=201)
async def create_user(
    user: Annotated[UserCreateSchema, Body(title="Create User")],
    db: Session = Depends(get_db),
):
    try:
        db_user = crud_user.create_user(db, user)
    except crud_user.UserAlreadyExistsException:
        raise HTTPException(
            status_code=409,
            detail=f"A user with this username ('{user.username}') already exists.",
        )
    access_token = create_access_token(data={"sub": db_user.username})
    return UserRegisterLoginSchema(
        user=UserReadSchema.model_validate(db_user),
        access_token=access_token,
        token_type="bearer",
    )


@router.post("/login", response_model=UserRegisterLoginSchema)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    db_user = crud_user.get_user_by_username(db, form_data.username)
    hashed_password = db_user.hashed_password if db_user else ""
    password_valid = verify_password(form_data.password, hashed_password)
    if not db_user or not password_valid:
        raise HTTPException(status_code=401, detail="Incorrect username or password.")
    access_token = create_access_token(data={"sub": db_user.username})
    # `model_validate` is used to convert the SQLAlchemy model to a Pydantic model for the response.
    # This ensures that the response adheres to the defined schema and only includes the fields specified in `UserReadSchema`.
    return UserRegisterLoginSchema(
        user=UserReadSchema.model_validate(db_user),
        access_token=access_token,
        token_type="bearer",
    )


ALLOWED_PROFILE_PICTURE_TYPES = ["image/jpeg", "image/png"]
MAX_PROFILE_PICTURE_SIZE = 5 * 1024 * 1024  # 5 MB


# Helper class to encapsulate the profile picture upload details.
@dataclass
class ProfilePictureUpload:
    filename: str
    file_bytes: bytes
    content_type: str
    url: str


# Validate the profile picture's type and size, then upload it to storage.
# If the picture is successfully uploaded, return a `ProfilePictureUpload` containing the upload details.
# Otherwise, raise an HTTPException.
async def validate_and_upload_profile_picture(
    profile_picture: UploadFile, user_id: int
) -> ProfilePictureUpload:
    picture_bytes = await profile_picture.read()
    if profile_picture.content_type not in ALLOWED_PROFILE_PICTURE_TYPES:
        raise HTTPException(status_code=415, detail="Invalid profile picture type.")
    if len(picture_bytes) > MAX_PROFILE_PICTURE_SIZE:
        raise HTTPException(status_code=413, detail="Profile picture is too large.")
    extension = profile_picture.content_type.split("/")[-1]
    filename = f"{user_id}_profile_picture.{extension}"
    try:
        url = upload_profile_picture(picture_bytes, filename)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Failed to upload profile picture due to internal issue.",
        )
    return ProfilePictureUpload(
        filename=filename,
        file_bytes=picture_bytes,
        content_type=profile_picture.content_type,
        url=url,
    )


# Verify if the uploaded profile picture contains NSFW content.
# If it does, delete the picture from storage and update the user profile accordingly. (url to None, is_nsfw to True, classification to None)
# Else, classify the picture and update the user profile with the classification result. (is_nsfw to False, classification to the classification result)
async def remove_if_nsfw_and_classify(
    upload: ProfilePictureUpload,
    user_id: int,
):
    db = SessionLocal()
    try:
        is_nsfw = await detect_nsfw_content(upload.file_bytes, upload.content_type)
        if is_nsfw:
            # 6. If the picture is NSFW, delete the picture from storage and update the user profile with `profile_picture_is_nsfw=True` and `profile_picture_classification=None`.
            crud_user_profile.set_user_profile_picture(db, user_id, None, True, None)
            delete_profile_picture(upload.filename)
        else:
            # 7. If the picture is not NSFW, update the user profile with `profile_picture_is_nsfw=False` and `profile_picture_classification` being the classification result.
            classification_result = await classify_image(
                upload.file_bytes, upload.content_type
            )
            crud_user_profile.set_user_profile_picture(
                db, user_id, upload.url, False, classification_result
            )
    finally:
        db.close()


@router.put("/profile", status_code=200, response_model=UserProfileReadSchema)
# `profile_data` is a string, which has to be manually converted to UserProfileCreateSchema.
# Reason: The request cannot contain both a JSON body and a multipart/form-data body. Hence, we solely rely on form data.
async def create_user_profile(
    background_tasks: BackgroundTasks,
    profile_data: Annotated[str, Form()],
    profile_picture: Annotated[UploadFile | None, File()] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Steps:
    # 1. Validate profile picture type and size
    # 2. Upload picture to storage
    # 3. Save profile data to db, with `profile_picture_is_nsfw` being None at the moment
    # 4. return response to user
    # 5. As background task, detect if profile picture is NSFW. If it is not, classify the picture.
    # 6. If the picture is NSFW, delete the picture from storage and update the user profile with `profile_picture_is_nsfw=True` and `profile_picture_classification=None`.
    # 7. If the picture is not NSFW, update the user profile with `profile_picture_is_nsfw=False` and `profile_picture_classification` being the classification result.

    # 1. Validate profile picture type and size, and upload to storage.
    upload: ProfilePictureUpload | None = None
    if profile_picture is not None:
        upload = await validate_and_upload_profile_picture(
            profile_picture, current_user.id
        )
    # 3. Save profile data to db, with `profile_picture_is_nsfw` being None at the moment
    user_profile_data = UserProfileCreateSchema.model_validate_json(profile_data)
    db_user_profile = crud_user_profile.upsert_user_profile(
        db,
        user_id=current_user.id,
        user_profile=user_profile_data,
        profile_picture_url=upload.url if upload is not None else None,
        profile_picture_is_nsfw=None,
        profile_picture_classification=None,
    )

    # 5-7. As background task, detect if profile picture is NSFW. If it is not, classify the picture.
    if upload is not None:
        # FastAPI's background tasks run after the response is sent.
        # As such, the user does not have to potentially wait a long time owing to the longer process of detecing NSFW content and classifying the profile picture.
        background_tasks.add_task(remove_if_nsfw_and_classify, upload, current_user.id)
    # 4. return response to user
    return db_user_profile


@router.get("/profile", status_code=200, response_model=UserProfileReadSchema)
async def read_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_user_profile = crud_user_profile.get_user_profile_by_user_id(db, current_user.id)
    if not db_user_profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return db_user_profile
