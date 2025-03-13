from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .routers import post,user,auth,votes,queryingpref,modifyingPref
from .database import engine
from mangum import Mangum



# models.Base.metadata.drop_all(bind=engine)




app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(votes.router)
app.include_router(queryingpref.router)
app.include_router(modifyingPref.router)

@app.get("/home")
def home():
    return {"message": "Hello from FastAPI on AWS Lambda!"}

handler = Mangum(app)

