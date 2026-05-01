from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from os import getenv

DATABASE_URL = (
    f"postgresql+psycopg2://{getenv('DB_USER')}:{getenv('DB_PASSWORD')}"
    f"@{getenv('DB_HOST')}:{getenv('DB_PORT')}/{getenv('DB_NAME')}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Enable the `pg_trgm` extension for PostgreSQL once the engine is connected.
# This extension is required for the trigram index on the `place_of_residence` column in the `user_profiles` table.
# See models/userProfile.py for more details on the index and its purpose.
# Taken from: https://docs.sqlalchemy.org/en/21/core/event.html
@event.listens_for(engine, "connect")
def enable_pg_trgm(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    cursor.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
