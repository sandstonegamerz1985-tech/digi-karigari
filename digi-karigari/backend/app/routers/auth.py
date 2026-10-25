from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import ArtisanProfile, User
from ..security import create_token, hash_password, verify_password
from ..serializers import serialize_user

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    role: Literal["buyer", "artisan"] = "buyer"  # admins cannot self-register
    # Only needed for artisans:
    craft: Optional[str] = Field(default=None, max_length=80)
    city: Optional[str] = Field(default=None, max_length=80)
    state: Optional[str] = Field(default="", max_length=80)
    bio: Optional[str] = Field(default="", max_length=600)

    @model_validator(mode="after")
    def artisan_needs_details(self):
        if self.role == "artisan" and (not (self.craft or "").strip() or not (self.city or "").strip()):
            raise ValueError("Artisans must provide their craft and city.")
        return self


class LoginIn(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(max_length=100)


@router.post("/register", status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower().strip()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    user = User(name=data.name.strip(), email=email, password_hash=hash_password(data.password), role=data.role)
    if data.role == "artisan":
        user.artisan_profile = ArtisanProfile(
            craft=data.craft.strip(),
            city=data.city.strip(),
            state=(data.state or "").strip(),
            bio=(data.bio or "").strip(),
            status="pending",  # an admin must approve before the Verified badge / listing rights
        )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_token(user.id, user.role), "token_type": "bearer", "user": serialize_user(user)}


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower().strip()))
    # Same message for "no such user" and "wrong password" so we do not leak which emails exist.
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return {"access_token": create_token(user.id, user.role), "token_type": "bearer", "user": serialize_user(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return serialize_user(user)
