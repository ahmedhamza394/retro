from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, join_room, leave_room
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
socketio = SocketIO(app)

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

@app.route('/create_session', methods=['POST'])
def create_session():
    session_name = request.json.get('session_name')
    session_password = request.json.get('session_password')

    if not session_name or len(session_name) == 0:
        return jsonify({'error': 'session_name can\'t be null'}), 400
    
    if not session_password or len(session_password) == 0:
        return jsonify({'error': 'session_password can\'t be null'}), 400
        
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO sessions (session_name, session_password) VALUES (%s, %s) RETURNING id", (session_name, session_password))
    session_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'session_id': session_id}), 201

@app.route('/join_session', methods=['POST'])
def join_session():
    session_id = request.json.get('session_id')
    session_password = request.json.get('session_password')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM sessions WHERE id = %s AND session_password = %s", (session_id, session_password))
    session_exists = cur.fetchone()
    cur.close()
    conn.close()
    if session_exists:
        return jsonify({'status': 'Session joined successfully'}), 200
    else:
        return jsonify({'error': 'Invalid session ID or password'}), 401

@app.route('/get_messages/<int:session_id>', methods=['GET'])
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
def handle_join_session(data):
    session_id = data.get('session_id')
    join_room(session_id)
    print(f"User joined session {session_id}")

@socketio.on('leave_session')
def handle_leave_session(data):
    session_id = data.get('session_id')
    leave_room(session_id)
    print(f"User left session {session_id}")

if __name__ == '__main__':
    socketio.run(app, debug=True)
