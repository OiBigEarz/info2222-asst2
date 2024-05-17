'''
db
database file, containing all the logic to interface with the sql database
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, joinedload
from models import *
from models import Article, Comment, User

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
def insert_user(username: str, password: str, isActive: bool, account_type: str, staff_type: None, isMuted: bool):
    with Session(engine) as session:
        user = User(username=username, password=password, isActive = isActive, account_type=account_type, staff_type=staff_type, isMuted = isMuted)
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
            
            friendInfo = []
            
            for friend in friends:
                if friend.user1.username == username:
                    friendInfo.append({
                        'username': friend.user2.username,
                        'isActive': friend.user2.isActive,
                        'account_type': friend.user2.account_type,
                        'staff_type': friend.user2.staff_type
                    })
            return friendInfo

def list_users():
    with Session(engine) as session:
        return session.query(User).all()

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

def insert_message(sender_username, receiver_username, room_id, text):
    with Session(engine) as session:
        message = Message(sender=sender_username, receiver=receiver_username, room_id=room_id, text=text)
        session.add(message)
        session.commit()

def get_messages(room_id):
    with Session(engine) as session:
        messages = session.query(Message).filter_by(room_id=room_id).order_by(Message.timestamp.asc()).all()
        return [(message.sender, message.text) for message in messages]

def delete_friendship(username, friend_username):
    with Session(engine) as session:
        friendship1 = session.query(Friendship).filter_by(user_1=username, user_2=friend_username).first()
        friendship2 = session.query(Friendship).filter_by(user_1=friend_username, user_2=username).first()
        if friendship1:
            session.delete(friendship1)
        if friendship2:
            session.delete(friendship2)
        session.commit()

def update_user_false(username: str):
     with Session(engine) as session:
         user = session.get(User, username)
         if user:
             user.isActive = False
             session.commit()
             
def update_user_true(username: str):
     with Session(engine) as session:
         user = session.get(User, username)
         if user:
             user.isActive = True
             session.commit()     

def insert_assignment(title, content, weight, filename):
    with Session(engine) as session:
        assignment = Assignment(title = title, content=content,  weight = weight, filename = filename)
        session.add(assignment)
        session.commit()   

def get_assignments():
    with Session(engine) as session:
        return session.query(Assignment).all()

def get_assignment(assignment_id):
    with Session(engine) as session:
        return session.query(Assignment).filter_by(id = assignment_id).one_or_none()

def update_assignment(assgn_id, title, content, weight):
    with Session(engine) as session:
        assignment = session.query(Assignment).filter_by(id = assgn_id).one_or_none()
        if assignment:
            assignment.title = title
            assignment.content = content
            assignment.weight = weight
            session.commit()
        else:
            raise ValueError("Assignment not found")

def delete_assignment(assgn_id):
    with Session(engine) as session:
        assignment = session.query(Assignment).filter_by(id = assgn_id).one_or_none()
        if assignment:
            session.delete(assignment)
            session.commit()
        else:
            raise ValueError("Assignment not found")

def insert_article(username, title, content, date):
    with Session(engine) as session:
        article = Article(title=title, content=content, author_username=username, date = date)
        session.add(article)
        session.commit()

def get_articles():
    with Session(engine) as session:
        return session.query(Article).options(joinedload(Article.author)).all()

def get_article(article_id):
    with Session(engine) as session:
        return session.query(Article).filter_by(id = article_id).one_or_none()

def insert_comment(username, article_id, content):
    with Session(engine) as session:
        comment = Comment(content=content, article_id=article_id, author_username=username)
        session.add(comment)
        session.commit()

def get_comments(article_id):
    with Session(engine) as session:
        comments = session.query(Comment).join(User, Comment.author_username == User.username).filter(Comment.article_id == article_id).all()
        result = []
        for comment in comments:
            comment_info = {
                'id': comment.id,
                'content': comment.content,
                'author_username': comment.author_username,
                'author_role': comment.author.account_type,  # Ensure this is a string
                'article_id': comment.article_id
            }
            result.append(comment_info)
        return result

def update_article(article_id, new_title, new_content):
    with Session(engine) as session:
        article = session.query(Article).filter_by(id=article_id).one_or_none()
        if article:
            article.title = new_title
            article.content = new_content
            session.commit()
        else:
            raise ValueError("Article not found")

def delete_article(article_id):
    with Session(engine) as session:
        article = session.query(Article).filter_by(id = article_id).one_or_none()
        if article:
            session.delete(article)
            session.commit()
        else:
            raise ValueError("Article not found")

def delete_comment(comment_id):
    with Session(engine) as session:
        comment = session.query(Comment).filter_by(id=comment_id).one_or_none()
        if not comment:
            return None  # Or some error message
        session.delete(comment)
        session.commit()

def update_user_false(username: str):
     with Session(engine) as session:
         user = session.get(User, username)
         if user:
             user.isActive = False
             session.commit()
             
def update_user_true(username: str):
     with Session(engine) as session:
         user = session.get(User, username)
         if user:
             user.isActive = True
             session.commit()
             
def update_user_muting(username: str):
     with Session(engine) as session:
         user = session.get(User, username)
         if user:
             user.isMuted = True
             session.commit()

def update_user_unmuting(username: str):
     with Session(engine) as session:
         user = session.get(User, username)
         if user:
             user.isMuted = False
             session.commit()            