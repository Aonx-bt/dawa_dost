"""Minimal auth shim for the hackathon MVP.

Real auth is Supabase Auth (see README). For local/demo use, every request
resolves to the seeded demo patient so the app works without a login flow.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

DEMO_PHONE = "+919999999999"
DEMO_NAME = "Rina Sharma"
DEMO_LANGUAGE = "hi-IN"


def get_or_create_demo_user(db: Session) -> User:
    user = db.query(User).filter(User.phone == DEMO_PHONE).first()
    if user:
        return user
    user = User(name=DEMO_NAME, phone=DEMO_PHONE, preferred_language=DEMO_LANGUAGE)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_current_user(db: Session = Depends(get_db)) -> User:
    # TODO(production): replace with Supabase Auth JWT verification and a
    # real user lookup by auth.uid(). Kept simple for the hackathon demo.
    return get_or_create_demo_user(db)
