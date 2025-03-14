import boto3
import json
import os
import logging

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

        for record in event.get("Records", []):
            body = json.loads(record.get("body", "{}"))  # Parse JSON safely
            logger.info(f"🔍 Processing message: {body}")

            # Extract the inner 'message' dictionary
            message_data = body.get("message", {})

            # Extract relevant fields
            post_owner_email = message_data.get("post_owner_email_id")
            phone_number = body.get("phone_number")  # This is outside "message"
            post_title = message_data.get("post_title", "Unknown Post")
            vote_direction = message_data.get("vote_direction", 0)

            # Validate input data
            if not post_owner_email and not phone_number:
                raise ValueError("Missing required fields: post_owner_email or phone_number")

            # Send email and SMS (handle partial failures)
            if post_owner_email:
                try:
                    send_email(post_owner_email, post_title, vote_direction)
                except Exception as e:
                    logger.error(f"❌ Error sending email: {str(e)}")

            if phone_number:
                try:
                    send_sms(phone_number, f"Your post '{post_title}' received a new like!")
                except Exception as e:
                    logger.error(f"❌ Error sending SMS: {str(e)}")

        return {"statusCode": 200, "body": json.dumps("Processed successfully")}

    except Exception as e:
        logger.error(f"❌ Error processing message: {str(e)}")
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}


def send_email(post_owner_email, post_title, vote_direction):
    message_text = f"Your post '{post_title}' received a {'like' if vote_direction == 1 else 'unlike'}"
    ses_client.send_email(
        Source=SOURCE_EMAIL,
        Destination={"ToAddresses": [post_owner_email]},
        Message={
            "Subject": {"Data": "New Vote Notification"},
            "Body": {"Text": {"Data": message_text}}
        }
    )
    logger.info(f"📧 Email sent to {post_owner_email}")


def send_sms(phone_number, message):
    sns_client.publish(
        PhoneNumber=phone_number,
        Message=message
    )
    logger.info(f"📩 SMS sent to {phone_number}")