from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_socketio import SocketIO, join_room, leave_room, emit
import psycopg2
import os
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
socketio = SocketIO(app)

# Rate limiter setup
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# Function to get a database connection
def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    return conn

@app.route('/')
def serve_index():
    return send_from_directory('templates', 'index.html')

@app.route('/sessions.html')
def serve_sessions():
    session_id = request.args.get('session_id')
    session_password = request.args.get('session_password')
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT session_id FROM sessions WHERE session_id = %s AND session_password = %s", (session_id, session_password))
        session_exists = cur.fetchone()
        cur.close()
        conn.close()
        if session_exists:
            return render_template('session.html', session_id=session_id, session_password=session_password)
        else:
            return jsonify({'error': 'Invalid session name or password'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    # Pass the session_id and session_password to the template
        

@app.route('/create_session', methods=['POST'])
@limiter.limit("1 per minute")  # Limit to 5 requests per minute per IP
def create_session():
    session_id = request.json.get('session_id')
    session_password = request.json.get('session_password')

    if not session_id or len(session_id) == 0:
        return jsonify({'error': 'session_id can\'t be null'}), 400

    if not session_password or len(session_password) == 0:
        return jsonify({'error': 'session_password can\'t be null'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO sessions (session_id, session_password) VALUES (%s, %s)", (session_id, session_password))
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        return jsonify({'error': 'session_name already exists'}), 400
    finally:
        cur.close()
        conn.close()

    return jsonify({'status': 'Session created successfully'}), 201

@app.route('/join_session', methods=['POST'])
@limiter.limit("10 per minute")  # Limit to 10 requests per minute per IP
def join_session():
    session_id = request.json.get('session_id')
    session_password = request.json.get('session_password')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT session_id FROM sessions WHERE session_id = %s AND session_password = %s", (session_id, session_password))
        session_exists = cur.fetchone()
        cur.close()
        conn.close()
        if session_exists:
            return jsonify({'status': 'Session joined successfully'}), 200
        else:
            return jsonify({'error': 'Invalid session name or password'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/add_message', methods=['POST'])
@limiter.limit("30 per minute")  # Limit to 30 requests per minute per IP
def add_message():
    session_id = request.json.get('session_id')
    message = request.json.get('message')
    category = request.json.get('category')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (session_id, message, category) VALUES (%s, %s, %s)", (session_id, message, category))
    conn.commit()
    cur.close()
    conn.close()
    
    print(session_id);

    socketio.emit('message_added', {'session_id': session_id, 'message': message, 'category': category}, room=session_id)
        
    return jsonify({'status': 'Message added'}), 201

@app.route('/get_messages/<string:session_id>', methods=['GET'])
def get_messages(session_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT message, category FROM messages WHERE session_id = %s", (session_id,))
        messages = cur.fetchall()
        cur.close()
        conn.close()

        messages_list = [{'message': msg[0], 'category': msg[1]} for msg in messages]

        return jsonify(messages_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@socketio.on('join_session')
def on_join(data):
    session_id = data['session_id']
    join_room(session_id)
    print(f"Joined room: {session_id}")

@socketio.on('leave_session')
def on_leave(data):
    session_id = data['session_id']
    leave_room(session_id)
    emit_user_count(session_id)

def emit_user_count(room):
    user_count = len(socketio.server.manager.rooms['/'][room])
    emit('user_count', {'count': user_count}, room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
