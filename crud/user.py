from sqlalchemy.orm import Session
from sqlalchemy import select
from schemas.user import UserCreateSchema
from models.user import User
from core.security import hash_password

class UserAlreadyExistsException(Exception):
    pass

def create_user(db: Session, user: UserCreateSchema):
    if get_user_by_username(db, user.username):
        raise UserAlreadyExistsException(f"User with username '{user.username}' already exists.")
    
    db_user = User(
        username=user.username.lower(),
        role="user",
        hashed_password=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str) -> User | None:
    return db.execute(select(User).where(User.username == username.lower())).scalar_one_or_none()
