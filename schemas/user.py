from pydantic import BaseModel, ConfigDict

from models.enums import UserRole


# Used for creating a new user
class UserCreateSchema(BaseModel):
    username: str
    password: str


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
