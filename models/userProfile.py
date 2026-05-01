from sqlalchemy import ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from database.base import Base
from models.enums import Gender


class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = (
        Index(
            "index_user_profile_place_of_residence_gin",
            "place_of_residence",
            postgresql_using="gin",  # Taken from: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#index-types
            postgresql_ops={
                "place_of_residence": "gin_trgm_ops"
            },  # Taken from: https://www.postgresql.org/docs/current/pgtrgm.html#PGTRGM-INDEX
        ),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    first_name: Mapped[str] = mapped_column()
    last_name: Mapped[str] = mapped_column()
    age: Mapped[int] = mapped_column(index=True)
    gender: Mapped[Gender] = mapped_column(index=True)
    place_of_residence: Mapped[str] = mapped_column()
    country_of_origin: Mapped[str] = mapped_column(index=True)
    description: Mapped[str | None] = mapped_column()
    profile_picture_url: Mapped[str | None] = mapped_column()
    profile_picture_classification: Mapped[str | None] = mapped_column()
    # `server_default` and `onupdate` ensure timestamps are automatically set/updated by the database.
    # `func.now()` is a SQLAlchemy function that generates the current timestamp in the database.
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )


# Brief overview of the indexes for this table's columns:
# - `user_id`: Primary key index (unique)
# - `age`: B-tree index (range queries)
# - `gender`: B-tree index (exact matching)
# - `place_of_residence`: GIN index with trigram ops (partial string matching)
#   - Partial matching must be used here, as examples may include `Berlin, Germany`, `France` and so on. In other words, the user has free-form input for this field.
#   - `GIN` is useful for `ILIKE` queries, with `trigram ops` enabling efficient trigram-based searching for partial matches.
#   - More specificaly, `GIN` stands for "Generalized Inverted Index" and is suitable for string-based columns where the values can differ greatly.
#   - As for `trigram ops`, it breaks down the string into trigrams (three-character sequences) and indexes those. The benefit is that we can support partial queries containing even typos.
# - `country_of_origin`: B-tree index (exact matching)
#   - Exact matching is used here, as the country of origin is a standardized ISO code that is always stored in the same format.

# For the exact matching and range queries, B-tree indexes are used.
# These are efficient for exact matching queries, as technically speaking, what is indexed is the value itself, rather than parts of the value as with the GIN index on `place_of_residence`..
# A B-tree index is also useful for range-based queries, e.g. minAge < x < maxAge, as well as exact age matching, as the values are stored in a sorted manner that allows for efficient traversal to find the relevant entries in the tree.
