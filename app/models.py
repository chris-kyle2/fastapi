from .database import Base, engine
from sqlalchemy import Column, Integer, String, Boolean,TIMESTAMP
from sqlalchemy.sql import text
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    published = Column(Boolean, server_default='TRUE', nullable=False)
    rating = Column(Integer, nullable=True, default=0)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,server_default=text('now()'))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("User")
class User(Base):
    __tablename__= "users"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    email = Column(String,nullable =False,unique= True)
    password = Column(String,nullable =False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,server_default=text('now()'))

class Vote(Base):
    __tablename__ = "votes"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)

class NotificationPreferences(Base):
    __tablename__ = "notification_preferences"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    sms_enabled = Column(Boolean, nullable=False, server_default="false")
    webhook_enabled = Column(Boolean, nullable=False, server_default="false")   
    webhook_url = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False,server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False,server_default=text('now()'), onupdate=text('now()'))
    user = relationship("User")



def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {str(e)}")

if __name__ == "__main__":
    create_tables()