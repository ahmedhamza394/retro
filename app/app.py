from flask import Flask
from flask_socketio import SocketIO
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import os
from app.routes.html_routes import *
from app.routes.api_routes import *
from app.socket_events import *

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
socketio = SocketIO(app)

# Rate limiter setup
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

if __name__ == '__main__':
    socketio.run(app, debug=True)
