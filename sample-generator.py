# Run this script to generate sample data for testing and development purposes.
# Command: docker-compose --profile seed run --rm seeder
import random
from faker import Faker
from pydantic_extra_types.country import CountryAlpha2
from models.enums import Gender, UserRole
from schemas.user import UserCreateSchema
from schemas.userProfile import UserProfileCreateSchema
from database.session import SessionLocal
from database.base import Base
from database.session import engine
from crud.user import create_user, UserAlreadyExistsException
from crud.userProfile import upsert_user_profile

# create tables if they don't exist
Base.metadata.create_all(bind=engine)

fake = Faker()


def seed():
    db = SessionLocal()
    try:
        # 1 admin user
        try:
            admin = create_user(
                db, UserCreateSchema(username="administrator", password="password")
            )
            admin.role = UserRole.admin
            db.commit()
            print(
                "Admin user created with username 'administrator' and password 'password'."
            )
        except UserAlreadyExistsException:
            print("Admin already exists, skipping.")
            admin = None

        if admin:
            upsert_user_profile(
                db,
                admin.id,
                UserProfileCreateSchema(
                    first_name="Admin",
                    last_name="User",
                    age=30,
                    gender=Gender.male,
                    country_of_origin=CountryAlpha2("US"),
                    place_of_residence="New York, USA",
                ),
            )

        # 10 regular users
        for _ in range(10):
            try:
                user = create_user(
                    db,
                    UserCreateSchema(
                        username=fake.unique.user_name(), password="password"
                    ),
                )
                print(
                    f"User created with username '{user.username}' and password 'password'."
                )
                upsert_user_profile(
                    db,
                    user.id,
                    UserProfileCreateSchema(
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        age=random.randint(18, 70),
                        gender=random.choice(
                            [Gender.male, Gender.female, Gender.other]
                        ),
                        country_of_origin=CountryAlpha2(fake.country_code()),
                        place_of_residence=fake.city(),
                    ),
                )
            except UserAlreadyExistsException:
                pass  # skip duplicate usernames

        print("Sample data generation complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
