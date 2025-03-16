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
load_dotenv()

# sqs_client = boto3.client(
#     "sqs",
#     region_name="us-east-1",
#     aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#     aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
# )
# ses_client = boto3.client(
#     "ses",
#     region_name="us-east-1",
#     aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#     aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
# )
# sns_client = boto3.client(
#     "sns",
#     region_name="us-east-1",
#     aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#     aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
# )
sqs_client = boto3.client("sqs", region_name="us-east-1") 
ses_client = boto3.client("ses", region_name="us-east-1")
sns_client = boto3.client("sns", region_name="us-east-1")

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

@router.post("",status_code=status.HTTP_201_CREATED)
def vote(vote: schema.Vote, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    post = db.query(models.Post).filter(models.Post.id == vote.post_id).first()
    print(post)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id {vote.post_id} not found")
    post_owner = db.query(models.User).filter(models.User.id == post.user_id).first()
    post_owner_email = post_owner.email
    print(f"Post ID: {post.id}")
    print(f"Post owner ID: {post.user_id}")
    print(f"Post owner email: {post_owner_email}")
    print(f"Current user email: {current_user.email}")
    vote_query = db.query(models.Vote).filter(models.Vote.post_id == vote.post_id, models.Vote.user_id == current_user.id)
    found_vote = vote_query.first()
    if vote.dir == 1:
        if found_vote:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"user {current_user.id} has already voted on post {vote.post_id}")
        new_vote = models.Vote(post_id = vote.post_id, user_id = current_user.id)
        db.add(new_vote)
        db.commit()
        message = {
        "post_owner_email_id": post_owner_email,
        "voter_email_id": current_user.email,
        "post_title": post.title,
        "post_id": post.id,
        "vote_direction": vote.dir,
        "timestamp": str(datetime.now())  # Add timestamp to ensure message uniqueness
          }
        sqs_client.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message))
        preference = get_post_owner_preference(db,post_owner.id)
        print(preference)
        print(f"phone number: {preference.phone_number}")
        if preference and preference.sms_enabled and preference.phone_number:
            send_message_to_sqs(preference.phone_number,message)
        return {"message": f"Post was liked by the user {current_user.id}"}
        
        
    else:
        if not found_vote:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vote does not exist")
        vote_query.delete(synchronize_session=False)
        db.commit()
        message = {
                "post_owner_email_id": post_owner_email,
                "voter_email_id": current_user.email,
                "post_title": post.title,
                "post_id": post.id,
                "vote_direction": vote.dir
        }
        print(message)
        sqs_client.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message))
        preference = get_post_owner_preference(db,post_owner.id)
        if preference and preference.sms_enabled and preference.phone_number:
            send_message_to_sqs( preference.phone_number,message)
        return {"message": f"Post was disliked by the user{current_user.id}"}
        
def send_message_to_sqs(phone_number: str,message: str):
    try:
        message = {
            "phone_number": phone_number,
            "message": message
        }
        sqs_client.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message))
    except Exception as e:
        print(f"Error sending message to SQS: {str(e)}")

   
    
    

def purge_queue():
    try:
        sqs_client.purge_queue(QueueUrl=QUEUE_URL)
        print("Queue purged successfully")
    except Exception as e:
        print(f"Error purging queue: {str(e)}")
    
    
    
