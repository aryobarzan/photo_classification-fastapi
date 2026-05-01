from typing import Annotated

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from schemas.user import UserCreateSchema, UserReadSchema, UserRegisterLoginSchema
from schemas.userProfile import UserProfileCreateSchema, UserProfileReadSchema
from database.session import get_db
from sqlalchemy.orm import Session
import crud.user as crud_user
import crud.userProfile as crud_user_profile
from core.security import create_access_token, verify_password
from core.dependencies import get_current_user
from models.user import User
from core.storage import upload_profile_picture

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


@router.put("/profile", status_code=200, response_model=UserProfileReadSchema)
# `profile_data` is a string, which has to be manually converted to UserProfileCreateSchema.
# Reason: The request cannot contain both a JSON body and a multipart/form-data body. Hence, we solely rely on form data.
async def create_user_profile(
    profile_data: Annotated[str, Form()],
    profile_picture: Annotated[UploadFile | None, File()] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile_picture_url = None
    if profile_picture is not None:
        profile_picture_bytes = await profile_picture.read()
        # Verify the profile picture's content type and size before proceeding.
        if profile_picture.content_type not in ALLOWED_PROFILE_PICTURE_TYPES:
            raise HTTPException(status_code=415, detail="Invalid profile picture type.")
        if len(profile_picture_bytes) > MAX_PROFILE_PICTURE_SIZE:
            raise HTTPException(status_code=413, detail="Profile picture is too large.")
        profile_picture_type_extension = profile_picture.content_type.split("/")[-1]
        profile_picture_filename = (
            f"{current_user.id}_profile_picture.{profile_picture_type_extension}"
        )
        try:
            profile_picture_url = upload_profile_picture(
                profile_picture_bytes, profile_picture_filename
            )
        except Exception:
            raise HTTPException(
                status_code=503,
                detail="Failed to upload profile picture due to internal issue.",
            )

    user_profile_data = UserProfileCreateSchema.model_validate_json(profile_data)
    db_user_profile = crud_user_profile.upsert_user_profile(
        db,
        user_id=current_user.id,
        user_profile=user_profile_data,
        profile_picture_url=profile_picture_url,
    )

    return db_user_profile
