'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''
"comment used for checking git commit"
from flask import Flask, render_template, request, abort, url_for, jsonify, redirect, current_app
from flask_socketio import SocketIO
from flask_cors import CORS
import db
import secrets
from werkzeug.security import check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, set_access_cookies, unset_jwt_cookies, jwt_required, get_jwt_identity , exceptions


# import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)
app = Flask(__name__)
CORS(app) 

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

# Configure JWT
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # Change to your secret key
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_SECURE'] = True  # Set to True in production with HTTPS
app.config['JWT_COOKIE_CSRF_PROTECT'] = True  # Enable CSRF protection

jwt = JWTManager(app) 

# don't remove this!!
import socket_routes

# index page
@app.route("/")
def index():
    return render_template("index.jinja")

@app.errorhandler(exceptions.NoAuthorizationError)
def handle_auth_error(e):
    return redirect(url_for('login'))

# login page
@app.route("/login")
def login():    
    return render_template("login.jinja")

# handles a post request when the user clicks the log in button
@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        return jsonify({"login": False, "msg": "Invalid request format"}), 400

    username = request.json.get("username")
    password = request.json.get("password")

    try:
        user = db.get_user(username)
        if user is None:
            return jsonify({"login": False, "msg": "User does not exist!"}), 404

        # Ensure this comparison is what you intend it to be
        if not check_password_hash(user.password, password):
            return jsonify({"login": False, "msg": "Password does not match!"}), 401

        access_token = create_access_token(identity=username)
        response = jsonify({'login': True, "msg": "Login successful"})
        set_access_cookies(response, access_token)
        return response
    except Exception as e:
        return jsonify({"login": False, "msg": str(e)}), 500


# handles a get request to the signup page
@app.route("/signup")
def signup():
    return render_template("signup.jinja")

# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        return jsonify({"msg": "Request must be JSON"}), 400

    username = request.json.get("username")
    password = request.json.get("password")
    public_key = request.json.get("public_key")
    salt = request.json.get("salt")  # Retrieve the salt from the request

    if not username or not password or not public_key or not salt:
        return jsonify({"msg": "Missing required parameters"}), 400

    if db.get_user(username) is not None:
        return jsonify({"msg": "User already exists!"}), 409

    # Ensure all required arguments are passed to the insert_user function
    db.insert_user(username, password, public_key, salt)
    access_token = create_access_token(identity=username)
    response = jsonify({'signup': True})
    set_access_cookies(response, access_token)
    return response

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

# home page, where the messaging app is
@app.route("/home")
@jwt_required()
def home():
    current_user = get_jwt_identity()  # Get the identity of the current user from JWT
    friends = db.list_friends(current_user)
    received_requests, sent_requests = db.list_friend_requests(current_user)

    return render_template("home.jinja", username=current_user, friends=friends,
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
@jwt_required()
def get_messages(username, receiver):
    # Ensure the user requesting is the same as the session user
    current_user = get_jwt_identity()
    if username != current_user:
        return jsonify({"error": "Unauthorized"}), 401
    messages = db.get_messages_between_users(username, receiver)
    return jsonify([{"message": message.message, "sender": message.sender, "timestamp": message.timestamp.isoformat()} for message in messages])

@app.route('/get_salt/<username>', methods=['GET'])
def get_salt(username):
    user = db.get_user(username)
    if user and hasattr(user, 'salt') and user.salt:
        return jsonify({"salt": user.salt}), 200
    else:
        return jsonify({"error": "User not found or salt unavailable"}), 404
    
@app.route('/send-message', methods=['POST'])
def send_message():
    if not request.is_json:
        return jsonify({"error": "Invalid content type"}), 415
    
    data = request.get_json()
    try:
        db.insert_message(data['sender'], data['receiver'], data['encryptedMessage'], data['iv'])
        return jsonify({"success": True})
    except Exception as e:
        current_app.logger.error(f"Exception during message insert: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500



#if __name__ == '__main__':
#    socketio.run(app, host = 'localhost', port = 1204)