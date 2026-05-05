from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from schemas.userProfile import UserProfileCreateSchema
from models.userProfile import UserProfile
from models.enums import Gender


class UserProfileDoesNotExistException(Exception):
    pass


# `upsert` as the user profile will either be created if the given user does not have one yet, or the existing user profile will be replaced with the new data.
def upsert_user_profile(
    db: Session,
    user_id: int,
    user_profile: UserProfileCreateSchema,
    profile_picture_filename: str | None = None,
    profile_picture_is_nsfw: bool | None = None,
    profile_picture_classification: str | None = None,
):
    # Upsert approach inspired by: https://docs.sqlalchemy.org/en/21/dialects/postgresql.html#insert-on-conflict-upsert
    user_profile_data = user_profile.model_dump()
    if profile_picture_filename is not None:
        user_profile_data["profile_picture_filename"] = profile_picture_filename
    if profile_picture_is_nsfw is not None:
        user_profile_data["profile_picture_is_nsfw"] = profile_picture_is_nsfw
    if profile_picture_classification is not None:
        user_profile_data["profile_picture_classification"] = (
            profile_picture_classification
        )
    # `insert` will attempt to create a new user profile.
    # `values(...)` specifies the user profile data itself, including the `user_id`.
    # If `insert` fails due to a conflict, i.e., an entry with the same `user_id` already exists, `on_conflict_do_update` will be triggered.
    # `index_elements=["user_id"]` indicates based on which column the conflict should be decided`.
    statement = (
        insert(UserProfile)
        .values(user_id=user_id, **user_profile_data)
        .on_conflict_do_update(index_elements=["user_id"], set_=user_profile_data)
    )
    db.execute(statement)
    db.commit()
    # Retrieve the upserted user profile
    return db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    ).scalar_one()


def set_user_profile_picture(
    db: Session,
    user_id: int,
    profile_picture_filename: str | None,
    profile_picture_is_nsfw: bool | None = None,
    profile_picture_classification: str | None = None,
) -> UserProfile:
    db_user_profile = db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    ).scalar_one_or_none()
    if not db_user_profile:
        raise UserProfileDoesNotExistException(
            f"User profile for user with id '{user_id}' does not exist."
        )
    db_user_profile.profile_picture_filename = profile_picture_filename
    db_user_profile.profile_picture_is_nsfw = profile_picture_is_nsfw
    db_user_profile.profile_picture_classification = profile_picture_classification
    db.commit()
    db.refresh(db_user_profile)
    return db_user_profile


def get_user_profile_by_user_id(db: Session, user_id: int) -> UserProfile | None:
    return db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    ).scalar_one_or_none()


def get_user_profiles(
    db: Session,
    min_age: int | None = None,
    max_age: int | None = None,
    exact_age: int | None = None,
    genders: list[Gender] | None = None,
    place_of_residence: str | None = None,
    country_of_origin: str | None = None,
) -> list[UserProfile]:
    statement = select(UserProfile)
    if exact_age is not None:
        statement = statement.where(UserProfile.age == exact_age)
    else:
        if min_age is not None:
            statement = statement.where(UserProfile.age >= min_age)
        if max_age is not None:
            statement = statement.where(UserProfile.age <= max_age)
    if genders:
        statement = statement.where(UserProfile.gender.in_(genders))
    if place_of_residence is not None:
        # `ilike` is used for case-insensitive pattern matching.
        # `%` is a wildcard for any sequence of characters, i.e., this allows for partial matching of the place of residence, rather than requiring exact matches.
        # For example, a search for `luxembourg` would match both `Luxembourg City, Luxembourg` and `Mamer, Luxembourg`.
        statement = statement.where(
            UserProfile.place_of_residence.ilike(f"%{place_of_residence}%")
        )
    if country_of_origin is not None:
        statement = statement.where(UserProfile.country_of_origin == country_of_origin)
        # TODO: offset for pagination
    return list(db.execute(statement.limit(100)).scalars().all())
