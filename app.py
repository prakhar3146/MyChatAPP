from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO, send, emit
from flask_mysqldb import MySQL
import datetime as dt
import re
from utils import hash_password,check_password

app = Flask(__name__)
app.secret_key = "Hello12345"

# MySQL DB Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'flask_users'

mysql = MySQL(app)

# Enable SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

dict_of_user = {}

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('welcome', {'message': 'Welcome to the server!'})

@socketio.on('disconnect')
def handle_disconnect():
    username = dict_of_user.pop(request.sid, None)
    if username:
        print(f"User disconnected: {username}")
        emit('user-disconnected', {'message': f'{username} left the chat'}, broadcast=True, include_self=False)
        #redirect(url_for('login'))

@socketio.on('logout-disconnect')
def logout_disconnect():
    username = dict_of_user.pop(request.sid, None)
    if username:
        print(f"User disconnected: {username}")
        emit('user-disconnected', {'message': f'{username} left the chat'}, broadcast=True, include_self=False)
        redirect(url_for('login'))

@socketio.on('new-user-joined')
def print_username(name):
    print("Username:", name, request.sid)
    dict_of_user[request.sid] = name
    emit('user-joined', {'message': f'{name} joined the chat at \n {dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'}, broadcast=True, include_self=False)

@socketio.on("send")
def send_message(message):
    sender = dict_of_user.get(request.sid)
    print("for req sid:", request.sid)
    print("Current User sent this message:", sender, "\n in dict:", dict_of_user)
    message = message + "\n at " + dt.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    print("Sender:", sender, "\nmessage:", dict_of_user)
    emit('recieve', {'message': message, 'name': sender}, broadcast=True, include_self=False)

@app.route("/")
def home():
    if 'username' in session:
        return redirect(url_for('message'))
    else:
        return render_template("home.html")

@app.route("/home")
def message():
    if 'username' in session:
        return render_template("message.html", username=session['username'])
    else:
        return redirect(url_for('home'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        pattern = re.fullmatch(r"^(\w)+$",username)
        if not pattern: 
            return render_template('login.html', error="Only Alphanumeric Characters are allowed in the Username!")
       
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT username, password FROM chat_app_users WHERE username=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        #Comparing the user provided password with the hashed password stored in the database
        match_pwd = check_password(hashed_password=user[1].encode('utf-8'), user_entered_password= password)
        if user and match_pwd:
            session['username'] = user[0]
            return redirect(url_for('message'))
        else:
            return render_template('login.html', error="Invalid Username or Password")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
        cursor = mysql.connection.cursor()
        # Regular expression to allow only alphanumeric characters and underscores 
        pattern = re.fullmatch(r"^(\w)+$",username) 
        if not pattern: 
            return render_template('register.html', error="Only Alphanumeric Characters are allowed in the Username!")
        #Check if the password is not empty
        if len(password) < 8:
            return render_template('register.html', error="The password has to be a minimum of 8 characters")
        
        if password!=confirm_password:
            return render_template('register.html', error="The entred password and the confirm password sections did not match!")
        #Checking if the username already exists
        cursor.execute("SELECT username FROM chat_app_users WHERE username=%s", (username,))
        user = cursor.fetchone()
        if user:
            return render_template('register.html', error="The username is already taken!\n Please try some other username")
        query = "INSERT INTO chat_app_users (username, password, joining_date) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, hash_password(password), dt.datetime.now()))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == "__main__":
    socketio.run(app, debug=True)
