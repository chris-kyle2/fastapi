from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schema
from .. database import get_db
from fastapi import status, Depends, HTTPException, APIRouter
from ..utils import hash


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)



@router.post("/",status_code=status.HTTP_201_CREATED, response_model= schema.UserResponse)
def create_user(user: schema.User,db: Session= Depends(get_db)):
    hashed_password = hash(user.password)
    user.password = hashed_password
    user_dict = user.dict(exclude={'id'})
    new_user = models.User(**user_dict)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/{id}",response_model=schema.UserResponse)
def get_user_by_id(id: int,db:Session= Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"user with id: {id} was not found")
    return user