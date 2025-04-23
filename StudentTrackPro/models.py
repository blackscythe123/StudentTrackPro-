from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(10), nullable=False)  # 'student' or 'faculty'
    
    # Relationship with student or faculty profile
    student = db.relationship('Student', backref='user', uselist=False, cascade="all, delete-orphan")
    faculty = db.relationship('Faculty', backref='user', uselist=False, cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    year_of_study = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    
    # Relationships
    enrollments = db.relationship('CourseEnrollment', backref='student', lazy=True, cascade="all, delete-orphan")
    attendance_records = db.relationship('Attendance', backref='student', lazy=True, cascade="all, delete-orphan")
    absence_requests = db.relationship('AbsenceRequest', backref='student', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Student {self.student_id}>'

class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    faculty_id = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    
    # Relationships
    courses = db.relationship('Course', backref='instructor', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Faculty {self.faculty_id}>'

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    schedule = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    min_attendance_percent = db.Column(db.Float, default=75.0, nullable=False)
    
    # Relationships
    enrollments = db.relationship('CourseEnrollment', backref='course', lazy=True, cascade="all, delete-orphan")
    sessions = db.relationship('CourseSession', backref='course', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Course {self.course_code}>'

class CourseEnrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='unique_enrollment'),
    )
    
    def __repr__(self):
        return f'<CourseEnrollment {self.student_id}-{self.course_id}>'

class CourseSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    title = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='session', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<CourseSession {self.course_id} on {self.session_date}>'

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('course_session.id'), nullable=False)
    status = db.Column(db.String(10), nullable=False)  # 'present', 'absent', 'late', 'excused'
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'session_id', name='unique_attendance'),
    )
    
    def __repr__(self):
        return f'<Attendance {self.student_id}-{self.session_id}: {self.status}>'

class AbsenceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    request_date = db.Column(db.Date, nullable=False)
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=False)
    from_time = db.Column(db.Time, nullable=True)  # New field
    to_time = db.Column(db.Time, nullable=True)    # New field
    reason = db.Column(db.Text, nullable=False)
    documentation = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='pending')
    response_notes = db.Column(db.Text, nullable=True)
    responded_at = db.Column(db.DateTime, nullable=True)
    course = db.relationship('Course')
    
    def __repr__(self):
        return f'<AbsenceRequest {self.student_id} for {self.from_date} to {self.to_date}: {self.status}>'

class AttendanceNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    notified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    recovered = db.Column(db.Boolean, default=False, nullable=False)  # Tracks if they recovered after notification
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='unique_notification'),
    )
    
    def __repr__(self):
        return f'<AttendanceNotification {self.student_id}-{self.course_id}: {"Recovered" if self.recovered else "Notified"}>'

# New Model: TeacherAbsenceNotification
class TeacherAbsenceNotification(db.Model):
    __tablename__ = 'teacher_absence_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    period = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notified_at = db.Column(db.DateTime, default=datetime.utcnow)

    faculty = db.relationship('Faculty', backref=db.backref('absence_notifications', lazy=True))
    course = db.relationship('Course', backref=db.backref('absence_notifications', lazy=True))
    
    def __repr__(self):
        return f'<TeacherAbsenceNotification {self.faculty_id} for {self.date}: {self.period}>'