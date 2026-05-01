from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base
from models.enums import UserRole

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(unique=True)
    role: Mapped[UserRole] = mapped_column(default=UserRole.user)
    hashed_password: Mapped[str] = mapped_column()