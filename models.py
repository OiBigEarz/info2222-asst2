'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Text, DateTime
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from typing import Dict
from datetime import datetime

# data models
Base = declarative_base()

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
    public_key: Mapped[str] = mapped_column(Text)
    salt: Mapped[str] = mapped_column(String)  # Adding salt column
    
class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    sender = Column(String, ForeignKey('user.username'))
    receiver = Column(String, ForeignKey('user.username'))
    message = Column(Text)  # This will store the encrypted message text
    iv = Column(String)  # Store the IV used in encryption
    timestamp = Column(DateTime, default=datetime.utcnow)  # Automatically sets the timestamp

    # Define relationships to the User model for easier access to user objects
    sender_user = relationship("User", foreign_keys=[sender])
    receiver_user = relationship("User", foreign_keys=[receiver])

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
        # dictionary that maps the username to the room id
        # for example self.dict["John"] -> gives you the room id of 
        # the room where John is in
        self.dict: Dict[str, int] = {}

    def create_room(self, sender: str, receiver: str) -> int:
        room_id = self.counter.get()
        self.dict[sender] = room_id
        self.dict[receiver] = room_id
        return room_id
    
    def join_room(self,  sender: str, room_id: int) -> int:
        self.dict[sender] = room_id

    def leave_room(self, user):
        if user not in self.dict.keys():
            return
        del self.dict[user]

    # gets the room id from a user
    def get_room_id(self, user: str):
        if user not in self.dict.keys():
            return None
        return self.dict[user]


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

    
