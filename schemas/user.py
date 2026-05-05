from pydantic import BaseModel, ConfigDict, Field

from models.enums import UserRole


# Used for creating a new user
class UserCreateSchema(BaseModel):
    username: str = Field(min_length=4, max_length=32, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(min_length=8, max_length=64)


# Used for reading user data
# Excludes the password for security reasons
class UserReadSchema(BaseModel):
    id: int
    username: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


# Used for returning user data after registration/login, includes access token (JWT)
class UserRegisterLoginSchema(BaseModel):
    user: UserReadSchema
    access_token: str
    token_type: str = "bearer"
