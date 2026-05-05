from fastapi import APIRouter, Depends, HTTPException
from schemas.userProfile import UserProfileReadSchema
from database.session import get_db
from sqlalchemy.orm import Session
import crud.userProfile as crud_user_profile
from core.dependencies import get_current_admin_user
from models.enums import Gender

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin_user)]
)


@router.get(
    "/users/profile/{user_id}", status_code=200, response_model=UserProfileReadSchema
)
async def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    db_user_profile = crud_user_profile.get_user_profile_by_user_id(db, user_id)
    if not db_user_profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return db_user_profile


@router.get(
    "/users/profiles", status_code=200, response_model=list[UserProfileReadSchema]
)
async def get_user_profiles(
    min_age: int | None = None,
    max_age: int | None = None,
    exact_age: int | None = None,
    genders: list[Gender] | None = None,
    place_of_residence: str | None = None,
    country_of_origin: str | None = None,
    db: Session = Depends(get_db),
):
    return crud_user_profile.get_user_profiles(
        db, min_age, max_age, exact_age, genders, place_of_residence, country_of_origin
    )
