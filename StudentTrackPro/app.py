import os
import logging
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_migrate import Migrate  # Add this import
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize extensions (without app yet)
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
migrate = Migrate()  # Initialize Migrate

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///attendance_system.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'priyagovinth2019@gmail.com'
app.config['MAIL_PASSWORD'] = 'cluzskufpjhfrgog'
app.config['MAIL_DEFAULT_SENDER'] = 'priyagovinth2019@gmail.com'

# Initialize extensions with the app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
csrf.init_app(app)
mail.init_app(app)
migrate.init_app(app, db)  # Initialize Migrate with app and db
print("Mail initialized:", hasattr(app, 'mail'))  # Debug statement

with app.app_context():
    # Import models here to avoid circular import
    from models import User, Student, Faculty, Course, Attendance, AbsenceRequest, CourseEnrollment, CourseSession, TeacherAbsenceNotification  # Add TeacherAbsenceNotification
    from routes import register_routes
    register_routes(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/get_attendance_percentage', methods=['GET'])
    def get_attendance_percentage():
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        total_sessions = Attendance.query.filter_by(session_id=session_id).count()
        if total_sessions == 0:
            return jsonify({'percentage': 0.0})
        
        present_count = Attendance.query.filter_by(session_id=session_id, status='present').count()
        percentage = (present_count / total_sessions) * 100
        return jsonify({'percentage': percentage})

if __name__ == '__main__':
    app.run(debug=True)