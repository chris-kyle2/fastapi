import json
import boto3
from pywebpush import webpush, WebPushException
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from . import models
import os
pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)

def verify(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_post_owner_preference(db: Session,post_owner_id: int):
    preference = db.query(models.NotificationPreferences).filter(models.NotificationPreferences.user_id == post_owner_id).first()
    return preference

def get_vapid_private_key(secret_name: str = "vapid_private_key"):
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    return response["SecretString"]

def send_web_push(subscription_info: dict, payload: dict):
    vapid_private_key = get_vapid_private_key()
    print(vapid_private_key)

    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=os.getenv('VAPID_PRIVATE_KEY'),
            vapid_claims={"sub": "mailto:adarshpandey57@gmail.com"}
        )
        return {"status": "sent"}
    except WebPushException as ex:
        return {
            "status": "error",
            "message": str(ex),
            "http_code": ex.response.status_code if ex.response else 500
        }
    
