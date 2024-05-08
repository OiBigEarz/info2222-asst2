'''
socket_routes
file containing all the routes related to socket.io
'''


from flask_socketio import join_room, emit, leave_room
from flask import request

try:
    from __main__ import socketio
except ImportError:
    from app import socketio

from models import Room

import db

room = Room()

# when the client connects to a socket
# this event is emitted when the io() function is called in JS
@socketio.on('connect')
def connect():
    username = request.cookies.get("username")
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
    # socket automatically leaves a room on client disconnect
    # so on client connect, the room needs to be rejoined
    join_room(int(room_id))
    emit("incoming", (f"{username} has connected", "green"), to=int(room_id))

# event when client disconnects
# quite unreliable use sparingly
@socketio.on('disconnect')
def disconnect():
    username = request.cookies.get("username")
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
    emit("incoming", (f"{username} has disconnected", "red"), to=int(room_id))

# send message event handler
@socketio.on("send")
def send(username, receiver, message, room_id):
    db.insert_message(username, receiver, room_id, message)
    emit("incoming", (f"{username}: {message}"), to=room_id)
    
# join room event handler
# sent when the user joins a room
@socketio.on("join")
def join(sender_name, receiver_name):
    
    receiver = db.get_user(receiver_name)
    if receiver is None:
        return "Unknown receiver!"  # Consider using `emit` for errors too, if it suits your client handling
    
    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"

    # Retrieve or create a consistent room ID for these two users
    room_id = room.get_room_id(sender_name, receiver_name)
    if room_id is None:
        room_id = room.create_room(sender_name, receiver_name)

    # If the room ID is valid, the user joins the room
    join_room(room_id)
    emit("incoming", (f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green"), to=room_id)

    # After joining, send the message history to the room
    messages = db.get_messages(room_id)
    for sender, msg in messages:
        emit("incoming", (f"{sender}: {msg}"), room=room_id)

    return room_id


# leave room event handler
@socketio.on("leave")
def leave(username, room_id):
    emit("incoming", (f"{username} has left the room.", "red"), to=room_id)
    leave_room(room_id)
    room.leave_room(username)
