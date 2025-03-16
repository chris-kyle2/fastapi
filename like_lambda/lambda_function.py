import boto3
import json
import os
import logging
import requests

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize boto3 clients
region_name = os.environ.get("AWS_REGION", "us-east-1")
ses_client = boto3.client("ses", region_name=region_name)
sns_client = boto3.client("sns", region_name=region_name)
SOURCE_EMAIL = os.environ["SOURCE_EMAIL"]


def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        print("event",event)

        for record in event.get("Records", []):
            body = json.loads(record.get("body", "{}"))  # Parse JSON safely
            logger.info(f"🔍 Processing message: {body}")
            print("body",body)

            post_owner_email = body.get("post_owner_email_id")
            voter_email = body.get("voter_email_id")
            post_title = body.get("post_title")
            vote_direction = body.get("vote_direction")
            preference = body.get("preference")
            
            
            if preference.get("webhook_enabled"):
                send_webhook(preference.get("webhook_url"),body)
            
            if preference.get("sms_enabled"):
                try:
                    send_sms(preference.get("phone_number"),f"Your post '{post_title}' received a new like! {voter_email}")
                except Exception as e:
                    logger.error(f"❌ Error sending SMS: {str(e)}")
            if post_owner_email:
                try:
                    send_email(post_owner_email, post_title, vote_direction,voter_email)
                except Exception as e:
                    logger.error(f"❌ Error sending email: {str(e)}")

        return {"statusCode": 200, "body": json.dumps("Processed successfully")}

    except Exception as e:
        logger.error(f"❌ Error processing message: {str(e)}")
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}


def send_email(post_owner_email, post_title, vote_direction,voter_email):
    message_text = f"Your post '{post_title}' received a {'like' if vote_direction == 1 else 'unlike'} from {voter_email}"
    ses_client.send_email(
        Source=SOURCE_EMAIL,
        Destination={"ToAddresses": [post_owner_email]},
        Message={
            "Subject": {"Data": "New Vote Notification"},
            "Body": {"Text": {"Data": message_text}}
        }
    )
    logger.info(f"📧 Email sent to {post_owner_email}")


def send_sms(phone_number,post_title,voter_email):
    sns_client.publish(
        PhoneNumber=phone_number,
        Message=f"Your post '{post_title}' received a new like! {voter_email}"
    )
    logger.info(f"📩 SMS sent to {phone_number}")

def send_webhook(webhook_url, body):
    try:
        response = requests.post(webhook_url, json=body, timeout=5)
        response.raise_for_status()  # Raises an error for bad status codes
        logger.info(f"🔗 Webhook sent to {webhook_url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Webhook failed for {webhook_url}: {str(e)}")