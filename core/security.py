import jwt
from fastapi import HTTPException, status
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from os import getenv
from pathlib import Path

password_hash = PasswordHash.recommended()
ALGORITHM = "RS256"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRIVATE_KEY_PATH = Path(getenv("JWT_PRIVATE_KEY_PATH") or PROJECT_ROOT / "private.pem")
PUBLIC_KEY_PATH = Path(getenv("JWT_PUBLIC_KEY_PATH") or PROJECT_ROOT / "public.pem")
DEFAULT_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day


@lru_cache
def _load_key(path: Path) -> str:
    try:
        return path.read_text()
    except OSError as e:
        raise RuntimeError(f"Could not read JWT key file '{path}': {e}") from e


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=DEFAULT_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, _load_key(PRIVATE_KEY_PATH), algorithm=ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, _load_key(PUBLIC_KEY_PATH), algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token."
            )
        return payload
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token."
        )
