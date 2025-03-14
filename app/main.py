from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .routers import post, user, auth, votes, queryingpref, modifyingPref
from .database import engine
from mangum import Mangum
import logging
import json





# models.Base.metadata.drop_all(bind=engine)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


app = FastAPI()
  # For production, replace with specific domain(s)

@app.middleware("http")
async def log_request(request: Request, call_next):
    logger.info(json.dumps({"method": request.method, "url": str(request.url)}))
    response = await call_next(request)
    return response

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Only allow your function URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)





@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/home")
def home():
    return {"message": "Hello from FastAPI on AWS Lambda!"}

app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(votes.router)
app.include_router(queryingpref.router)
app.include_router(modifyingPref.router)



handler = Mangum(app, lifespan="off")


