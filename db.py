'''
db
database file, containing all the logic to interface with the sql database
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import *
from werkzeug.security import generate_password_hash


from pathlib import Path

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# change it if you wish
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=False)

# initializes the database
Base.metadata.create_all(engine)

# inserts a user to the database
def insert_user(username: str, password: str):
    hashed_password = generate_password_hash(password)
    with Session(engine) as session:
        user = User(username=username, password=hashed_password)
        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)
    
def send_friend_request(sender_username: str, receiver_username: str):
    with Session(engine) as session:
        friend_request = FriendRequest(sender=sender_username, receiver=receiver_username, status='pending')
        session.add(friend_request)
        session.commit()

def accept_friend_request(request_id: int):
    with Session(engine) as session:
        friend_request = session.get(FriendRequest, request_id)
        if friend_request and friend_request.status == 'pending':
            friend_request.status = 'accepted'
            friendship = Friendship(user_1=friend_request.sender, user_2=friend_request.receiver)
            session.add(friendship)
            session.commit()

def reject_friend_request(request_id: int):
    with Session(engine) as session:
        friend_request = session.get(FriendRequest, request_id)
        if friend_request and friend_request.status == 'pending':
            friend_request.status = 'rejected'
            session.commit()

def list_friends(username: str):
    with Session(engine) as session:
        user = session.get(User, username)
        if user:

            friends = session.query(Friendship).filter(
                (Friendship.user_1 == username) | (Friendship.user_2 == username)).all()
            # Extract friend usernames from friendships
            friend_usernames = [
                friend.user2.username if friend.user1.username == username else friend.user1.username 
                for friend in friends
            ]
            return friend_usernames

def list_friend_requests(username: str):
    with Session(engine) as session:
        received_requests = session.query(FriendRequest).filter(
            FriendRequest.receiver == username, 
            FriendRequest.status == 'pending'
        ).all()
        sent_requests = session.query(FriendRequest).filter(
            FriendRequest.sender == username,
            FriendRequest.status == 'pending'
        ).all()
        return received_requests, sent_requests

