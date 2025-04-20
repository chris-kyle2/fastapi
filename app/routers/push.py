from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schema, models
from ..database import get_db
from ..oauth2 import get_current_user
from app.utils import send_web_push

router = APIRouter(
    prefix="/push",
    tags=["Push Notifications"]
)

@router.post("/subscribe")
def save_subscription(
    subscription: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Optionally save the subscription to the database (if you want to send notifications later)
    
    # For now, just return success
    return {"message": "Subscription saved"}
