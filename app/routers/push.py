from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from .. import schema, models
from ..database import get_db
from ..oauth2 import get_current_user

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
    try:
        # Try to get the existing preferences
        prefs = db.query(models.NotificationPreferences).filter(
            models.NotificationPreferences.user_id == current_user.id
        ).one()
    except NoResultFound:
        # If not found, create a new preference row
        prefs = models.NotificationPreferences(user_id=current_user.id)

    # Update push subscription fields
    prefs.push_enabled = True
    prefs.push_endpoint = subscription.get("endpoint")
    prefs.push_p256dh = subscription.get("keys", {}).get("p256dh")
    prefs.push_auth = subscription.get("keys", {}).get("auth")

    db.add(prefs)
    db.commit()

    return {"message": "Push subscription saved"}
