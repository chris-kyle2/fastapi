import boto3
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Initialize AWS clients
ses_client = boto3.client("ses", region_name="us-east-1")
sns_client = boto3.client("sns", region_name="us-east-1")

# Configuration
SOURCE_EMAIL = os.environ["SOURCE_EMAIL"]
DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]
MILESTONES = [2, 3, 4] 

def lambda_handler(event, context):
    try:
        print(f" Received event: {event}")

        # Process each SQS message
        for record in event["Records"]:
            # Parse the message body
            body = json.loads(record["body"])
            print(f"🔍 Processing message: {body}")

            # Check if it's an Email or SMS notification
            if "post_owner_email_id" in body:  # Email notification
                send_email(body)
            elif "phone_number" in body:  # SMS notification
                send_sms(body)
            else:
                print(" Unknown message format, skipping")
        check_milestone_likes()

        return {"statusCode": 200, "body": json.dumps(" Processed successfully")}

    except Exception as e:
        print(f" Error processing message: {str(e)}")
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}


def send_email(body):
    try:
        post_owner_email = body["post_owner_email_id"]
        voter_email = body["voter_email_id"]
        message_text = f"Your post '{body['post_title']}' received a {'like' if body['vote_direction'] == 1 else 'unlike'}"

        response = ses_client.send_email(
            Source=SOURCE_EMAIL,
            Destination={"ToAddresses": [post_owner_email]},
            Message={
                "Subject": {"Data": "New Vote Notification"},
                "Body": {"Text": {"Data": message_text}}
            }
        )
        
        print(f"📧 Email sent to {post_owner_email}: {response}")

    except Exception as e:
        print(f" Error sending email: {str(e)}")


def send_sms(body):
    try:
        phone_number = body["phone_number"]
        message = body["message"]

        response = sns_client.publish(
            PhoneNumber=phone_number,
            Message=message
        )

        print(f"SMS sent to {phone_number}: {response}")

    except Exception as e:
        print(f"Error sending SMS: {str(e)}")

def check_milestone_likes():
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Query to find posts reaching milestones
        query = """
        SELECT posts.id, posts.title, users.email, COUNT(votes.post_id) as like_count
        FROM posts
        JOIN votes ON posts.id = votes.post_id
        JOIN users ON posts.user_id = users.id
        GROUP BY posts.id, users.email
        HAVING COUNT(votes.post_id) IN %s;
        """
        cursor.execute(query, (tuple(MILESTONES),))
        milestone_posts = cursor.fetchall()

        for post in milestone_posts:
            post_title = post['title']
            like_count = post['like_count']
            user_email = post['email']

            message = f"🎉 Congrats! Your post '{post_title}' reached {like_count} likes!"

            # Send Email Notification
            ses_client.send_email(
                Source=SOURCE_EMAIL,
                Destination={"ToAddresses": [user_email]},
                Message={
                    "Subject": {"Data": "Milestone Achieved!"},
                    "Body": {"Text": {"Data": message}}
                }
            )
            print(f"🏆 Milestone email sent to {user_email}")

        # Close DB connection
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error checking milestones: {str(e)}")


