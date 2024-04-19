'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''
"comment used for checking git commit"
from flask import Flask, render_template, request, abort, url_for, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import db
import secrets
from werkzeug.security import check_password_hash


# import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)
app = Flask(__name__)
CORS(app) 

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

# don't remove this!!
import socket_routes

# index page
@app.route("/")
def index():
    return render_template("index.jinja")

# login page
@app.route("/login")
def login():    
    return render_template("login.jinja")

# handles a post request when the user clicks the log in button
@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    password = request.json.get("password")

    user = db.get_user(username)
    if user is None:
        return "Error: User does not exist!"

    # Check if hashed password matches
    if not check_password_hash(user.password, password):
        return "Error: Password does not match!"

    return url_for('home', username=username)


# handles a get request to the signup page
@app.route("/signup")
def signup():
    return render_template("signup.jinja")

# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        abort(404)
    username = request.json.get("username")
    password = request.json.get("password")
    public_key = request.json.get("public_key")  # Retrieve the public key from the request

    if db.get_user(username) is None:
        db.insert_user(username, password, public_key)  # Pass the public key to your insert function
        return url_for('home', username=username)
    return "Error: User already exists!"

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

# home page, where the messaging app is
@app.route("/home")
def home():
    username = request.args.get("username")
    if username is None:
        abort(404)

    # Fetch friends and friend requests
    friends = db.list_friends(username)
    received_requests, sent_requests = db.list_friend_requests(username)

    return render_template("home.jinja", username=username, friends=friends,
                           received_requests=received_requests, sent_requests=sent_requests)


# Route to send a friend request
@app.route("/add-friend", methods=["POST"])
def add_friend():
    if not request.is_json:
        abort(400)  # Bad Request

    sender = request.json.get("sender")
    receiver = request.json.get("receiver")
    
    # You might want to add checks here to ensure both users exist
    db.send_friend_request(sender, receiver)
    return "Friend request sent successfully!", 200

# Route to list all friends for a user
@app.route("/list-friends/<username>")
def list_friends(username):
    friends = db.list_friends(username)
    return render_template("friends_list.jinja", friends=friends, username=username)

# Route to accept a friend request
@app.route("/accept-friend-request", methods=["POST"])
def accept_friend_request():
    if not request.is_json:
        abort(400)  # Bad Request
    
    request_id = request.json.get("request_id")
    db.accept_friend_request(request_id)
    return "Friend request accepted!", 200

# Route to reject a friend request
@app.route("/reject-friend-request", methods=["POST"])
def reject_friend_request():
    if not request.is_json:
        abort(400)  # Bad Request
    
    request_id = request.json.get("request_id")
    db.reject_friend_request(request_id)
    return "Friend request rejected", 200

@app.route("/get-public-key/<username>", methods=["GET"])
def get_public_key(username):
    print("Fetching public key for:", username)
    user = db.get_user(username)
    if user is None:
        print("User not found:", username)
        return jsonify({"error": "User not found"}), 404
    print("Public key found:", user.public_key)
    return jsonify({"public_key": user.public_key}), 200

@app.route("/get-messages/<username>/<receiver>", methods=["GET"])
def get_messages(username, receiver):
    messages = db.get_messages_between_users(username, receiver)
    return jsonify([{"message": message.message, "sender": message.sender, "timestamp": message.timestamp.isoformat()} for message in messages])

#if __name__ == '__main__':
#    socketio.run(app, host = 'localhost', port = 1204)