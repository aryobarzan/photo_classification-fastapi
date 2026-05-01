from sqlalchemy.orm import DeclarativeBase

# Base class for SQLAlchemy models
# Models inheriting this class will define their mapping to database tables using `__tablename__` and column definitions.
# `Base.metadata` will be used to create the database schema based on the defined models.
# This class does not contain any attributes or methods itself, but serves as a common ancestor for all ORM models in the application.
class Base(DeclarativeBase):
    pass