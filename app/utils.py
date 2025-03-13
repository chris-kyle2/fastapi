from passlib.context import CryptContext
from sqlalchemy.orm import Session
from . import models
pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)

def verify(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_post_owner_preference(db: Session,post_owner_id: int):
    preference = db.query(models.NotificationPreferences).filter(models.NotificationPreferences.user_id == post_owner_id).first()
    return preference
    
