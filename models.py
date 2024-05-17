'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Dict
from datetime import datetime

# data models
class Base(DeclarativeBase):
    pass

# model to store user information
class User(Base):
    __tablename__ = "user"
    # looks complicated but basically means
    # I want a username column of type string,
    # and I want this column to be my primary key
    # then accessing john.username -> will give me some data of type string
    # in other words we've mapped the username Python object property to an SQL column of type String 
    username: Mapped[str] = mapped_column(String, primary_key=True)
    password: Mapped[str] = mapped_column(String)
    isActive = Column(Boolean, default = False)
    account_type = Column(String)  # 'Student' or 'Staff'
    staff_type = Column(String)    # 'Academic', 'Administrative', 'Admin', or None
    articles = relationship("Article", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    isMuted = Column(Boolean, default = False)

# stateful counter used to generate the room id
class Counter():
    def __init__(self):
        self.counter = 0
    
    def get(self):
        self.counter += 1
        return self.counter

# Room class, used to keep track of which username is in which room
class Room():
    def __init__(self):
        self.counter = Counter()
        self.rooms: Dict[tuple, int] = {}

    def get_sorted_users(self, user1, user2):
        return tuple(sorted([user1, user2]))

    def create_room(self, user1, user2):
        key = self.get_sorted_users(user1, user2)
        if key not in self.rooms:
            self.rooms[key] = self.counter.get()
        return self.rooms[key]

    def get_room_id(self, user1, user2):
        key = self.get_sorted_users(user1, user2)
        return self.rooms.get(key, None)

class Friendship(Base):
    __tablename__ = "friendship"
    
    id = Column(Integer, primary_key=True)
    user_1 = Column(String, ForeignKey('user.username'))
    user_2 = Column(String, ForeignKey('user.username'))
    
    # Define relationships to the User model
    user1 = relationship("User", foreign_keys=[user_1])
    user2 = relationship("User", foreign_keys=[user_2])

class FriendRequest(Base):
    __tablename__ = "friend_request"
    
    id = Column(Integer, primary_key=True)
    sender = Column(String, ForeignKey('user.username'))
    receiver = Column(String, ForeignKey('user.username'))
    status = Column(Enum('pending', 'accepted', 'rejected', name='request_status'))
    
    # Define relationships to the User model
    sender_user = relationship("User", foreign_keys=[sender])
    receiver_user = relationship("User", foreign_keys=[receiver])

class Message(Base):
    __tablename__ = 'message'
    
    id = Column(Integer, primary_key=True)
    sender = Column(String, ForeignKey('user.username'))
    receiver = Column(String, ForeignKey('user.username'))
    room_id = Column(Integer)
    text = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sender_user = relationship("User", foreign_keys=[sender])
    receiver_user = relationship("User", foreign_keys=[receiver])

class Assignment(Base):
    __tablename__ = 'assignment'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(String)
    weight = Column(Integer)
    filename = Column(String)

class Article(Base):
    __tablename__ = 'article'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(String)
    date = Column(DateTime, default = datetime.utcnow)
    author_username = Column(String, ForeignKey('user.username'))
    author = relationship("User", back_populates="articles")
    comments = relationship("Comment", back_populates="article")


class Comment(Base):
    __tablename__ = 'comment'
    id = Column(Integer, primary_key=True)
    content = Column(String)
    article_id = Column(Integer, ForeignKey('article.id'))
    author_username = Column(String, ForeignKey('user.username'))
    article = relationship("Article", back_populates="comments")
    author = relationship("User", back_populates="comments")

