from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schema, models
from ..database import get_db
from ..oauth2 import get_current_user
from app.utils import send_web_push

router = APIRouter(
    prefix="/subscribe",
    tags=["Push Notifications"]
)

@router.post("")
def save_push_subscription(
    subscription: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Save the subscription info into the DB or some persistent storage
    # For now, just log or store in memory (as a placeholder)
    print(f"User {current_user.email} subscribed with: {subscription}")
    
    # You could also create a DB model to store this and associate with user.id
    return {"message": "Subscription saved"}
