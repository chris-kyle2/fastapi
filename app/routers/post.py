from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from .. import models, schema
from .. database import  get_db
from typing import List
from .. import oauth2
from typing import Optional
from sqlalchemy import func
router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)


@router.get("", response_model=List[schema.PostVote])
def get_posts(db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user), limit: int = 10, skip: int = 0, search: Optional[str] = ""):
    results = db.query(models.Post, func.count(models.Vote.post_id).label("votes"))\
        .join(models.Vote, models.Post.id == models.Vote.post_id, isouter=True)\
        .group_by(models.Post.id)\
        .filter(models.Post.title.contains(search))\
        .offset(skip)\
        .limit(limit)\
        .all()
    return results
    


@router.post("/create", status_code=status.HTTP_201_CREATED,response_model=schema.PostResponse)
def create_post(post: schema.Post, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    # Convert Pydantic model to dict and exclude id (auto-generated)
    post_dict = post.dict(exclude={'id'})
    
    # Create new post
    print(current_user)
    print(post_dict)
    new_post = models.Post(user_id=current_user.id,**post_dict)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    return new_post


@router.get("/{id}",response_model=schema.PostVote)
def get_post_by_id(id: int, db: Session = Depends(get_db),current_user: int = Depends(oauth2.get_current_user)):
    print(current_user.email)
    post = db.query(models.Post, func.count(models.Vote.post_id).label("votes"))\
        .join(models.Vote, models.Post.id == models.Vote.post_id, isouter=True)\
        .group_by(models.Post.id,models.Post.user_id)\
        .filter(models.Post.id == id).first()
    print(post)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"post with id: {id} was not found")
    if post[0].user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                          detail=f"Not authorized to perform requested action")
    return post

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post_by_id(id: int, db: Session = Depends(get_db),current_user: models.User = Depends(oauth2.get_current_user)):
    print(current_user.email)
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()
    
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"post with id: {id} was not found")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                          detail=f"Not authorized to perform requested action")
    
    post_query.delete(synchronize_session=False)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{id}", status_code=status.HTTP_200_OK,response_model=schema.PostResponse)
def update_post_by_id(id: int, updated_post: schema.UpdatePost, db: Session = Depends(get_db),current_user: int = Depends(oauth2.get_current_user)):
    print(current_user.email)
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()
    
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"post with id: {id} was not found")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                          detail=f"Not authorized to perform requested action")
    
    post_query.update(updated_post.dict(exclude={'id'}), synchronize_session=False)
    db.commit()
    
    return post_query.first()

@router.patch("/{id}", status_code=status.HTTP_200_OK,response_model=schema.PostResponse)
def update_post_field_by_id(id: int, updated_post: schema.UpdatePost, db: Session = Depends(get_db),current_user: int = Depends(oauth2.get_current_user)):
    print(current_user.email)
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()
    
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"post with id: {id} was not found")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                          detail=f"Not authorized to perform requested action")
    
    update_data = updated_post.dict(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                          detail="At least one field must be provided for update")
    
    post_query.update(update_data, synchronize_session=False)
    db.commit()
    return post_query.first()
