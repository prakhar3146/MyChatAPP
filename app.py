from flask import Flask,render_template,request
from flask_socketio import SocketIO,send, emit
import sys
# sys.path.append("C:/Users/HP/PycharmProjects/python_chat_app/templates")
#Inititializing the application
app = Flask(__name__)


#Enable socket IO
socketio = SocketIO(app, cors_allowed_origins ="*")


list_of_users = []
dict_of_user= {}
#Adding Event Listener for connection
@socketio.on('connect') 
def handle_connect(): 
    print('Client connected') # Add your logic here, like emitting a welcome message or logging the connection emit('welcome', {'message': 'Welcome to the server!'})

#Adding Event Listener for disconnection
# Handle disconnection
@socketio.on('disconnect')
def handle_disconnect():
    user = dict_of_user.pop(request.sid, None)  # Remove the user from the dictionary
    if user:
        print(f"User disconnected: {user['name']}")
        emit('user-disconnected', {'message': f'{user["name"]} has left the chat'}, broadcast=True,include_self= False)
        


@socketio.on('new-user-joined')
def print_username(name):
    print("Username : ",name,request.sid)
    #send(message= f"New User Joined : \n{name}", broadcast = True)
    
    # Save user info with session ID as the key
    dict_of_user[request.sid] = name#{'id': request.sid, 'name': name}
    emit('user-joined', {'message': f'{name} joined the chat'},broadcast= True, include_self= False)



#Define event listener for messages
@socketio.on("send")
def send_message(message):
    #send(message=message, broadcast = True)
    
    if len(message.split(":"))==1:
        sender= dict_of_user.get(request.sid)

    # else:
    #     sender = message.split(":")[0]
    if sender:
        print("for req sid : ",request.sid)
        print("Current User sent this message",sender,"\n in dict : ",dict_of_user)
        sender=" you"
        
    # dict_of_user.get(request.sid, {'name': 'Unknown'})['name']
    print("Sender : ",sender,"/nmessage : ",dict_of_user)
    emit('recieve', {'message': message, 'name': sender}, broadcast=True, include_self= False)
    
    #Send function will emit a send event by default


#Define the route to render
@app.route("/")
def message():
    return render_template("message.html")


#Run the app
if __name__ == "__main__":
    app.run(debug= True)

