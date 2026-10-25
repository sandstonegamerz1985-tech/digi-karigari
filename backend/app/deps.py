"""Reusable FastAPI "dependencies" that answer: who is calling, and are they allowed?"""
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_token

_bearer = HTTPBearer(auto_error=False)


def get_optional_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Returns the logged-in user, or None if there is no valid token."""
    if not creds:
        return None
    data = decode_token(creds.credentials)
    if not data:
        return None
    return db.get(User, int(data["sub"]))


def get_current_user(user: Optional[User] = Depends(get_optional_user)) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to continue.")
    return user


def require_roles(*roles: str):
    """Usage: Depends(require_roles("admin")) -> only admins get through."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="You do not have permission to do this.")
        return user

    return checker


def require_approved_artisan(user: User = Depends(require_roles("artisan"))) -> User:
    profile = user.artisan_profile
    if not profile or profile.status == "pending":
        raise HTTPException(
            status_code=403,
            detail="Your artisan account is waiting for admin approval. You can add listings once it is approved.",
        )
    if profile.status == "rejected":
        raise HTTPException(
            status_code=403,
            detail="Your artisan application was rejected. Please contact the admin.",
        )
    return user
