from enum import Enum

class UserRole(str, Enum):
    admin = "admin"
    user = "user"

class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"