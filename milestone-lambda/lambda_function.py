import boto3
import os
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize boto3 clients
sns_client = boto3.client("sns", region_name="us-east-1")
ses_client = boto3.client("ses", region_name="us-east-1")

# Environment variables
SOURCE_EMAIL = os.environ["SOURCE_EMAIL"]
DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]
PROMO_SNS_TOPIC_ARN = os.environ["PROMO_SNS_TOPIC_ARN"]
MILESTONES = [10, 50, 100]  # Customize milestone values

def lambda_handler(event, context):
    try:
        logger.info("Running milestone & promotional notification check...")

        # Validate environment variables
        required_env_vars = ["SOURCE_EMAIL", "DB_HOST", "DB_NAME", "DB_USER", "DB_PASS", "PROMO_SNS_TOPIC_ARN"]
        for var in required_env_vars:
            if var not in os.environ:
                raise ValueError(f"Missing required environment variable: {var}")

        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check milestone likes
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

        # Send milestone emails
        for post in milestone_posts:
            try:
                ses_client.send_email(
                    Source=SOURCE_EMAIL,
                    Destination={"ToAddresses": [post["email"]]},
                    Message={
                        "Subject": {"Data": "🎉 Milestone Reached!"},
                        "Body": {"Text": {"Data": f"Your post '{post['title']}' reached {post['like_count']} likes!"}}
                    }
                )
                logger.info(f"Milestone email sent to {post['email']}")
            except Exception as e:
                logger.error(f"Error sending email to {post['email']}: {str(e)}")

        # Send promotional messages via SNS fanout
        promo_message = "🔥 Limited Offer: Get 20% off on premium features! Sign up now!"
        sns_client.publish(
            TopicArn=PROMO_SNS_TOPIC_ARN,
            Message=promo_message,
            Subject="Exclusive Offer!"
        )
        logger.info("Promotional email/SMS sent to all subscribers.")

        # Close DB connection
        cursor.close()
        conn.close()

        return {"statusCode": 200, "body": json.dumps("Milestone & promotional notifications sent")}

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}