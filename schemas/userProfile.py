from pydantic import BaseModel
from pydantic_extra_types.country import CountryAlpha2
from datetime import datetime

from models.enums import Gender


# Used for creating a new user profile
class UserProfileCreateSchema(BaseModel):
    first_name: str
    last_name: str
    age: int
    gender: Gender
    place_of_residence: str
    # `CountryAlpha2` ensures that only valid ISO 3166-1 alpha-2 country codes can be used, e.g., `US` or `DE`.
    country_of_origin: CountryAlpha2
    description: str | None = None


# Used for reading user profile data
# `created_at` and `updated_at` are generated server-side.
class UserProfileReadSchema(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    age: int
    gender: Gender
    place_of_residence: str
    country_of_origin: CountryAlpha2
    description: str | None = None
    profile_picture_url: str | None = None
    profile_picture_classification: str | None = None
    created_at: datetime
    updated_at: datetime
