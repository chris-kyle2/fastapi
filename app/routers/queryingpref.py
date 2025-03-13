from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schema
from ..database import get_db
from ..oauth2 import get_current_user

router = APIRouter(
    prefix="/preferences",
    tags=["Notification Preferences"]
)

@router.get("/", response_model=schema.NotificationPreferenceResponse)
def get_user_preferences(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    preference = db.query(models.NotificationPreferences).filter(models.NotificationPreferences.user_id == current_user.id).first()
    print(preference)
    
    if not preference:
        raise HTTPException(status_code=404, detail="Notification preference not found")
    
    return preference
