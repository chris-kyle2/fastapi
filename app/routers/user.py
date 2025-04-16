from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schema
from .. database import get_db
from fastapi import status, Depends, HTTPException, APIRouter
from ..utils import hash
import logging
import sys


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)



@router.post("/",status_code=status.HTTP_201_CREATED, response_model= schema.UserResponse)
def create_user(user: schema.User,db: Session= Depends(get_db)):
    try:
        print("Received request to create user.", flush=True)
        sys.stdout.flush()
        hashed_password = hash(user.password)
        user.password = hashed_password
        user_dict = user.dict(exclude={'id'})
        new_user = models.User(**user_dict)
        print(f"Prepared new user: {new_user}", flush=True)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"User created successfully: {new_user}", flush=True)
        logger.info(f"User created successfully: {new_user}")
        print(f"User created successfully: {new_user}")
        return new_user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        print(f"Error creating user: {e}")
        sys.stdout.flush()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error creating user: {e}")

@router.get("/{id}",response_model=schema.UserResponse)
def get_user_by_id(id: int,db:Session= Depends(get_db)):
    logger.info(f"Received request to fetch user with ID: {id}")
    print(f"Received request to fetch user with ID: {id}")
    sys.stdout.flush()
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"user with id: {id} was not found")
    logger.info(f"User found: {user.email}")
    print(f"User found: {user.email}")
    sys.stdout.flush()
    return user