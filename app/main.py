from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .routers import post, user, auth, votes, queryingpref, modifyingPref, push
from mangum import Mangum
import logging
import json
from .config import settings
import traceback

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


