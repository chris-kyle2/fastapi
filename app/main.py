from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .routers import post,user,auth,votes,queryingpref,modifyingPref
from .database import engine
from mangum import Mangum



# models.Base.metadata.drop_all(bind=engine)




app = FastAPI()
  # For production, replace with specific domain(s)

origins = [
    "https://s6lxblazkdroduvwr5kdndxfmq0qyzvu.lambda-url.us-east-1.on.aws"
]

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

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

handler = Mangum(app, lifespan="off")


