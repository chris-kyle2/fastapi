from pydantic import BaseModel,EmailStr,conint
from typing import Optional
from datetime import datetime
from pydantic.types import conint
from pydantic import Field
from typing import Annotated
class Post(BaseModel):
    title: str
    content: str
    published: bool = True
    rating: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    class Config:
        orm_mode = True
    

class UpdatePost(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    published: Optional[bool] = None
    rating: Optional[int] = None

class PostResponse(Post):
    id: int
    created_at: datetime
    user_id: int
    owner: UserResponse
    class Config:
        orm_mode = True

class PostVote(BaseModel):
    Post: PostResponse
    votes: int
    class Config:
        orm_mode = True

class User(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[int] = None

class Vote(BaseModel):
    post_id: int
    dir: Annotated[int,Field(le=1)]