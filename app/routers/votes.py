from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schema
from .. database import  get_db
from .. import oauth2
import boto3
import json
from datetime import datetime
import os
from dotenv import load_dotenv   
from ..utils import get_post_owner_preference
from pywebpush import webpush, WebPushException
import logging

load_dotenv()

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize boto3 clients
sqs_client = boto3.client("sqs", region_name="us-east-1") 
ses_client = boto3.client("ses", region_name="us-east-1")
sns_client = boto3.client("sns", region_name="us-east-1")

QUEUE_URL = os.getenv("SQS_QUEUE_URL")
SOURCE_EMAIL = os.getenv("SOURCE_EMAIL")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")

if not QUEUE_URL:
    raise RuntimeError("QUEUE_URL environment variable is missing!")
if not SOURCE_EMAIL:
    raise RuntimeError("SOURCE_EMAIL environment variable is missing!")
if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
    raise RuntimeError("VAPID keys are missing in environment variables!")

VAPID_CLAIMS = {
    "sub": "mailto:" + SOURCE_EMAIL
}

router = APIRouter(
    prefix="/votes",
    tags=["Votes"]
)

def send_push_notification(subscription_info, notification_data):
    try:
        logger.info(f"📱 Attempting to send push notification")
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(notification_data),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
        logger.info("✅ Push notification sent successfully")
        return True
    except WebPushException as e:
        logger.error(f"❌ Push notification failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error sending push notification: {str(e)}")
        return False

@router.post("", status_code=status.HTTP_201_CREATED)
def vote(vote: schema.Vote, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # Get the post and verify it exists
    post = db.query(models.Post).filter(models.Post.id == vote.post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id {vote.post_id} not found")
    
    # Get post owner details
    post_owner = db.query(models.User).filter(models.User.id == post.user_id).first()
    post_owner_email = post_owner.email

    # Check for existing vote
    vote_query = db.query(models.Vote).filter(models.Vote.post_id == vote.post_id, models.Vote.user_id == current_user.id)
    found_vote = vote_query.first()
    
    # Get post owner's preferences
    preference = get_post_owner_preference(db, post.user_id)
    if not preference:
        return {"message": f"No preference found for the post owner {post_owner.id}"}

    logger.info(f"Post owner preferences found: {preference.__dict__}")
    
    # Extract push subscription if it exists
    push_subscription = None
    if preference.push_enabled and preference.push_subscription:
        try:
            push_subscription = json.loads(preference.push_subscription)
            logger.info(f"Valid push subscription found for user {post_owner.id}")
        except json.JSONDecodeError:
            logger.error(f"Invalid push subscription format for user {post_owner.id}")
        except Exception as e:
            logger.error(f"Error processing push subscription: {str(e)}")

    # Prepare notification message
    action = "liked" if vote.dir == 1 else "removed their vote from"
    notification_title = "Vote Notification"
    notification_body = f"{current_user.email} has {action} your post: {post.title}"
    
    message = {
        "post_owner_email_id": post_owner_email,
        "voter_email_id": current_user.email,
        "post_title": post.title,
        "post_id": post.id,
        "vote_direction": vote.dir,
        "timestamp": str(datetime.now()),
        "notification_title": notification_title,
        "notification_body": notification_body,
        "preference": {
            "sms_enabled": preference.sms_enabled,
            "phone_number": preference.phone_number,
            "webhook_enabled": preference.webhook_enabled,
            "webhook_url": preference.webhook_url,
            "push_enabled": preference.push_enabled,
            "push_subscription": push_subscription
        }
    }

    try:
        if vote.dir == 1:
            if found_vote:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                                detail=f"user {current_user.id} has already voted on post {vote.post_id}")
            new_vote = models.Vote(post_id=vote.post_id, user_id=current_user.id)
            db.add(new_vote)
            db.commit()
            
            # Send push notification if enabled
            push_sent = False
            if push_subscription:
                notification_data = {
                    "title": notification_title,
                    "body": notification_body,
                    "data": {
                        "post_id": post.id,
                        "url": f"/posts/{post.id}"
                    }
                }
                push_sent = send_push_notification(push_subscription, notification_data)
                logger.info(f"Push notification {'sent successfully' if push_sent else 'failed'}")
            
            # Send other notifications via SQS
            response = sqs_client.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message))
            logger.info(f"SQS message sent successfully: {response}")
            
            return {
                "message": f"Post was liked by user {current_user.id}", 
                "notification_queued": True,
                "push_notification_sent": push_sent
            }
        else:
            if not found_vote:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vote does not exist")
            vote_query.delete(synchronize_session=False)
            db.commit()
            
            # Send push notification if enabled
            push_sent = False
            if push_subscription:
                notification_data = {
                    "title": notification_title,
                    "body": notification_body,
                    "data": {
                        "post_id": post.id,
                        "url": f"/posts/{post.id}"
                    }
                }
                push_sent = send_push_notification(push_subscription, notification_data)
                logger.info(f"Push notification {'sent successfully' if push_sent else 'failed'}")
            
            # Send other notifications via SQS
            response = sqs_client.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message))
            logger.info(f"SQS message sent successfully: {response}")
            
            return {
                "message": f"Vote was removed by user {current_user.id}", 
                "notification_queued": True,
                "push_notification_sent": push_sent
            }
    except Exception as e:
        logger.error(f"Error processing vote: {str(e)}")
        return {
            "message": f"Vote processed but notifications failed: {str(e)}", 
            "notification_queued": False,
            "push_notification_sent": False
        }

def purge_queue():
    try:
        sqs_client.purge_queue(QueueUrl=QUEUE_URL)
        logger.info("Queue purged successfully")
    except Exception as e:
        logger.error(f"Error purging queue: {str(e)}")
    
    
    
