from flask import jsonify, request
from app import app, limiter
from app.database import get_db_connection
import psycopg2


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