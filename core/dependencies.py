from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import crud.user as crud_user
from database.session import get_db
from sqlalchemy.orm import Session
from models.enums import UserRole
from models.user import User
from core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    payload = decode_token(token)
    user = crud_user.get_user_by_username(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token.")
    return user


def get_current_admin_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    user = get_current_user(token, db)
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin privileges required.")
    return user
