'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''
"comment used for checking git commit"
from flask import Flask, render_template, request, abort, url_for
from flask_socketio import SocketIO
import db
import secrets
from flask import jsonify
from datetime import datetime
import os
from werkzeug.utils import secure_filename



# import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

UPLOAD_FOLDER = "static"
ALLOWED_EXTENSIONS = {"pdf"}

app = Flask(__name__)

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

socketio = SocketIO(app)

# don't remove this!!
import socket_routes

# index page
@app.route("/")
def index():
    return render_template("login.jinja")

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

    if user.password != password:
        return "Error: Password does not match!"
    
    return url_for('home', username=request.json.get("username"))

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
    account_type = request.json.get("accountType")
    staff_type = request.json.get("staffType") if account_type == "Staff" else None
    isMuted = False
    
    existing_user = db.get_user(username)
    if existing_user:
        return "Error: User already exists!"
    
    isActive = True

    db.insert_user(username, password, isActive, account_type, staff_type, isMuted)
    return url_for('home', username=username)


# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    
    username = request.json.get("username")
    if not username:
        return "Invalid request", 400   
    db.update_user_false(username)
    
    return render_template('404.jinja'), 404

# home page, where the messaging app is
@app.route("/home")
def home():
    print("am here")
    username = request.args.get("username")
    
    user = db.get_user(username)

    if username is None:
        abort(404)

    user = db.get_user(username)
    if user is None:
        abort(404)  # Or redirect to login
        
    role = f"{user.account_type}" if not user.staff_type else f"{user.staff_type}"

    # Fetch friends and friend requests
    allUsers = db.list_users()
    friends = db.list_friends(username)
    received_requests, sent_requests = db.list_friend_requests(username)
    
    db.update_user_true(username)

    return render_template("home.jinja", username=username, isActive = user.isActive, friends=friends,
                           received_requests=received_requests, sent_requests=sent_requests, 
                           account_type = user.account_type, staff_type = user.staff_type, allUsers = allUsers, isMuted = user.isMuted)


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
    print(friends)
    return friends

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

@app.route("/delete-friend", methods=["POST"])
def delete_friend():
    if not request.is_json:
        return "Invalid request", 400

    username = request.json.get("username")
    friend_username = request.json.get("friend_username")

    if not username or not friend_username:
        return "Missing data", 400

    # Function to delete the friendship
    try:
        db.delete_friendship(username, friend_username)
        return "Friend removed successfully", 200
    except Exception as e:
        return str(e), 500

@app.route('/articles', methods=['POST'])
def create_article():
    if not request.is_json:
        abort(400)
    title = request.json.get("title")
    content = request.json.get("content")
    username = request.json.get("username")
    date = datetime.now()

    db.insert_article(username, title, content, date)
    return jsonify({"message": "Article created successfully!"}), 201

@app.route('/articles', methods=['GET'])
def get_articles():
    articles = db.get_articles()
    articles_data = []
    for article in articles:
        if article.author:
            articles_data.append({
                "id": article.id, 
                "title": article.title, 
                "content": article.content,
                "date": article.date, 
                "author_username": article.author.username, 
                "author_role": article.author.account_type if article.author else 'Unknown'
            })
        else:
            articles_data.append({
                "id": article.id, 
                "title": article.title, 
                "content": article.content, 
                "date": article.date, 
                "author_username": "Unknown", 
                "author_role": "Unknown"
            })

    return jsonify(articles_data)

@app.route('/comments', methods=['POST'])
def post_comment():
    if not request.is_json:
        abort(400)
    content = request.json.get("content")
    article_id = request.json.get("article_id")
    username = request.json.get("username")

    db.insert_comment(username, article_id, content)
    return jsonify({"message": "Comment added successfully!"}), 201

@app.route('/comments/<int:article_id>', methods=['GET'])
def get_comments_route(article_id):
    try:
        comments = db.get_comments(article_id)
        return jsonify(comments)
    except Exception as e:
        # Log the exception details to help diagnose the issue
        print(f"Error retrieving comments: {str(e)}")
        return jsonify({"error": "Failed to retrieve comments"}), 500

    
@app.route('/articles/<int:article_id>', methods=['PUT'])
def update_article(article_id):
    if not request.is_json:
        return jsonify({'message': 'Invalid request'}), 400

    try:
        new_title = request.json.get("title")
        new_content = request.json.get("content")
        username = request.json.get("username")

        user = db.get_user(username)
        article = db.get_article(article_id)
        if article is None:
            return jsonify({'message': 'Article not found'}), 404

        if article.author_username == username or (user and user.account_type == "Staff" and user.staff_type != "Student"):
            db.update_article(article_id, new_title, new_content)
            return jsonify({"message": "Article updated successfully!"}), 200
        else:
            return jsonify({"message": "Unauthorized"}), 403
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/articles/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    try:
        username = request.args.get("username")
        user = db.get_user(username)
        article = db.get_article(article_id)

        if article is None:
            return jsonify({'message': 'Article not found'}), 404

        if user and (user.account_type == "Staff" and user.staff_type != "Student" or article.author_username == username):
            db.delete_article(article_id)
            return jsonify({"message": "Article deleted successfully!"}), 200
        else:
            return jsonify({"message": "Unauthorized"}), 403
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    username = request.args.get("username")
    user = db.get_user(username)
    if user and user.account_type != "Student":
        try:
            db.delete_comment(comment_id)
            return jsonify({"message": "Comment deleted successfully!"}), 200
        except Exception as e:
            return jsonify({"message": str(e)}), 500
    else:
        return jsonify({"message": "Unauthorized"}), 403

@app.route("/logout-user", methods=["POST"])
def logout_user():
    if not request.is_json:
        abort(400) 
    username = request.json.get("username")
    if not username:
        return "Invalid request", 400   
    db.update_user_false(username)
    return url_for("index")

@app.route("/mute-user", methods=["POST"])
def mute_user():
    if not request.is_json:
        abort(400)   
    receiver = request.json.get("receiver")
    if not receiver:
        return "Invalid request", 400   
    db.update_user_muting(receiver)

    socketio.emit('mute-the-user', {'receiver': receiver})    
    return "Yep"

@app.route("/unmute-user", methods=["POST"])
def unmute_user():
    if not request.is_json:
        abort(400)   
    receiver = request.json.get("receiver")
    if not receiver:
        return "Invalid request", 400   
    db.update_user_unmuting(receiver)

    socketio.emit('unmute-the-user', {'receiver': receiver})    
    return "Yup"

@app.route("/post-assignment", methods = ["POST"])
def post_assignment():

    print("We made it to here!")

    title = request.form.get("title")
    content = request.form.get("content")
    weighting = request.form.get("weighting")
    asstFilename = request.form.get("filename")

    db.insert_assignment(title = title, content = content, 
                         weight = weighting, filename = asstFilename)
    

    file = request.files["file"]

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    return "Ahuh"

@app.route('/assignments', methods=['GET'])
def get_assignments():
    assignments = db.get_assignments()
    assignmentsdata = []
    for assignment in assignments:
        assignmentsdata.append({
            "id": assignment.id, 
            "title": assignment.title, 
            "content": assignment.content,
            "weight": assignment.weight, 
            "filename": assignment.filename 
        })       
    return jsonify(assignmentsdata)

@app.route('/assignments/<int:assignment_id>', methods=['DELETE'])
def delete_assignment(assignment_id):
    try:
        db.delete_assignment(assignment_id)
        return jsonify({"message": "Assignment deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/assignments/<int:assignment_id>', methods=['PUT'])
def update_assignment(assignment_id):
    try:
        new_title = request.json.get("title")
        new_content = request.json.get("content")
        new_weighting = request.json.get("weight")

        assignment = db.get_assignment(assignment_id)
        if assignment is None:
            return jsonify({'message': 'Assignment not found'}), 404

        db.update_assignment(assignment_id, new_title, new_content, new_weighting)
        return jsonify({"message": "Article updated successfully!"}), 200
       
    except Exception as e:  
        return jsonify({"message": str(e)}), 500
 
if __name__ == '__main__':
    socketio.run(app, host = 'localhost', port = 1204)