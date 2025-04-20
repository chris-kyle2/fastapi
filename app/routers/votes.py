from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schema
from ..database import get_db
from .. import oauth2
import boto3
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from ..utils import get_post_owner_preference, send_web_push, is_valid_push_subscription

load_dotenv()

sqs_client = boto3.client("sqs", region_name="us-east-1")

QUEUE_URL = os.getenv("SQS_QUEUE_URL")
SOURCE_EMAIL = os.getenv("SOURCE_EMAIL")

if not QUEUE_URL:
    raise RuntimeError("QUEUE_URL environment variable is missing!")
if not SOURCE_EMAIL:
    raise RuntimeError("SOURCE_EMAIL environment variable is missing!")

router = APIRouter(
    prefix="/votes",
    tags=["Votes"]
)

@router.post("", status_code=status.HTTP_201_CREATED)
def vote(
    vote: schema.Vote,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    post = db.query(models.Post).filter(models.Post.id == vote.post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id {vote.post_id} not found")

    post_owner = db.query(models.User).filter(models.User.id == post.user_id).first()
    if not post_owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post owner not found")

    vote_query = db.query(models.Vote).filter(
        models.Vote.post_id == vote.post_id,
        models.Vote.user_id == current_user.id
    )
    found_vote = vote_query.first()

    # Early exit on invalid actions
    if vote.dir == 1 and found_vote:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"user {current_user.id} has already voted on post {vote.post_id}"
        )
    elif vote.dir == 0 and not found_vote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vote does not exist"
        )

    # Perform DB action
    if vote.dir == 1:
        new_vote = models.Vote(post_id=vote.post_id, user_id=current_user.id)
        db.add(new_vote)
        action = "liked"
    else:
        vote_query.delete(synchronize_session=False)
        action = "removed their vote from"

    db.commit()

    # Notification preferences
    preference = get_post_owner_preference(db, post.user_id)
    if not preference:
        return {
            "message": f"Vote registered, but no preference found for post owner {post_owner.id}",
            "notification_sent": False
        }

    # Build the message
    message = {
        "post_owner_email_id": post_owner.email,
        "voter_email_id": current_user.email,
        "post_title": post.title,
        "post_id": post.id,
        "vote_direction": vote.dir,
        "timestamp": str(datetime.now()),
        "notification_title": "Vote Notification",
        "notification_body": f"{current_user.email} has {action} your post: {post.title}",
        "preference": {
            "sms_enabled": preference.sms_enabled,
            "phone_number": preference.phone_number,
            "webhook_enabled": preference.webhook_enabled,
            "webhook_url": preference.webhook_url,
            "push_enabled": preference.push_enabled,
            "push_endpoint": preference.push_endpoint,
            "push_p256dh": preference.push_p256dh,
            "push_auth": preference.push_auth
        }
    }

    # Send push notification
    notification_sent = False
    if is_valid_push_subscription(preference):
        subscription_info = {
            "endpoint": preference.push_endpoint,
            "keys": {
                "p256dh": preference.push_p256dh,
                "auth": preference.push_auth
            }
        }
        payload = {
            "title": message["notification_title"],
            "body": message["notification_body"],
            "url": f"/posts/{post.id}"
        }
        push_result = send_web_push(subscription_info, payload)
        notification_sent = push_result["status"] == "success"

        if not notification_sent:
            print(f"[Push Error] {push_result['message']}")
        else:
            print(f"[Push Success] Sent to {post_owner.email}")

    # Send message to SQS
    sqs_client.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message))

    return {
        "message": f"User {current_user.id} has {action} post {vote.post_id}",
        "notification_sent": notification_sent
    }

# Optional: manual purge for dev/debug
def purge_queue():
    try:
        sqs_client.purge_queue(QueueUrl=QUEUE_URL)
        print("Queue purged successfully")
    except Exception as e:
        print(f"Error purging queue: {str(e)}")
