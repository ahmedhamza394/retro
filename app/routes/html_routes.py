from flask import send_from_directory, render_template, jsonify, request
from app import app
from app.database import get_db_connection
import psycopg2


@app.route('/')
def serve_index():
    return send_from_directory(app.config['TEMPLATES_FOLDER'], 'index.html')

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