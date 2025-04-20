from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .routers import post, user, auth, votes, queryingpref, modifyingPref, push
from mangum import Mangum
import logging
import json
from .config import settings
import traceback
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# CORS middleware configuration
origins = ["https://d1dnaki3okqf9b.cloudfront.net"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Request logging middleware with error handling
@app.middleware("http")
async def log_request(request: Request, call_next):
    try:
        logger.info(json.dumps({
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers)
        }))
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Add custom CORS headers for Lambda Function URL
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "https://d1dnaki3okqf9b.cloudfront.net"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
    return response

# Include all routers
app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(votes.router)
app.include_router(queryingpref.router)
app.include_router(modifyingPref.router)
app.include_router(push.router)

# AWS Lambda handler
handler = Mangum(app, lifespan="off")

# Add CORS headers to the Lambda handler
def lambda_handler(event, context):
    response = handler(event, context)
    
    # Ensure response is a dictionary
    if isinstance(response, dict):
        # Add CORS headers to the response
        if "headers" not in response:
            response["headers"] = {}
            
        response["headers"].update({
            "Access-Control-Allow-Origin": "https://d1dnaki3okqf9b.cloudfront.net",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type"
        })
    
    return response


