from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schema
from ..database import get_db
from ..oauth2 import get_current_user

router = APIRouter(
    prefix="/preferences",
    tags=["Notification Preferences"]
)

@router.put("", response_model=schema.NotificationPreferenceResponse)
def update_user_preferences(
    preference_update: schema.NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Fetch the user's notification preferences
    preference = db.query(models.NotificationPreferences).filter(
        models.NotificationPreferences.user_id == current_user.id
    ).first()

    if not preference:
        preference = models.NotificationPreferences(
            user_id=current_user.id,
            sms_enabled=preference_update.sms_enabled,
            webhook_enabled=preference_update.webhook_enabled,
            webhook_url=preference_update.webhook_url,
            phone_number=preference_update.phone_number,
            push_enabled=preference_update.push_enabled,
            push_endpoint=preference_update.push_endpoint,
            push_p256dh=preference_update.push_p256dh,
            push_auth=preference_update.push_auth
        )
        db.add(preference)
        db.commit()
        db.refresh(preference)
        return preference

    # Update fields only if provided
    if preference_update.sms_enabled is not None:
        preference.sms_enabled = preference_update.sms_enabled
    if preference_update.webhook_enabled is not None:
        preference.webhook_enabled = preference_update.webhook_enabled
    if preference_update.webhook_url is not None:
        preference.webhook_url = preference_update.webhook_url
    if preference_update.phone_number is not None:
        preference.phone_number = preference_update.phone_number
    if preference_update.push_enabled is not None:
        preference.push_enabled = preference_update.push_enabled
    if preference_update.push_endpoint is not None:
        preference.push_endpoint = preference_update.push_endpoint
    if preference_update.push_p256dh is not None:
        preference.push_p256dh = preference_update.push_p256dh
    if preference_update.push_auth is not None:
        preference.push_auth = preference_update.push_auth

    # Commit changes
    db.commit()
    db.refresh(preference)

    return preference  # FastAPI automatically converts this to a Pydantic model
