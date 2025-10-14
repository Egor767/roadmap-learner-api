import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBaseModel(BaseModel):
    id: uuid.UUID


class UserCreateModel(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserUpdateModel(BaseModel):
    username: str | None = None
    email: EmailStr | None = None


class UserPresentModel(UserBaseModel):
    username: str
    email: str
    created_at: datetime


class UserInDB(UserBaseModel):
    hashed_password: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

