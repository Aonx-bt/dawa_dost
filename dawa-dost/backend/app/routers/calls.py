from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Call, User
from app.schemas.schemas import CallOut
from app.utils.current_user import get_current_user

router = APIRouter(prefix="/api/calls", tags=["calls"])


@router.get("", response_model=list[CallOut])
def list_calls(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Call)
        .filter(Call.user_id == user.id)
        .order_by(Call.created_at.desc())
        .all()
    )
