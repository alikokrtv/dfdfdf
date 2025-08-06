from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler

# Database
db = SQLAlchemy()

# Login Manager
login_manager = LoginManager()

# Mail
mail = Mail()

# SocketIO
socketio = SocketIO()

# CSRF Protection
csrf = CSRFProtect()

# Migration
migrate = Migrate()

# Scheduler
scheduler = BackgroundScheduler() 