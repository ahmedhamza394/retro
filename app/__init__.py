from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['TEMPLATES_FOLDER'] = 'templates'

from app.routes.html_routes import *
from app.routes.api_routes import *
from app.socket_events import *
