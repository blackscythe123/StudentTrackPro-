from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms import TextAreaField, IntegerField, DateField, TimeField, FloatField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional
from models import User, Student, Faculty, Course  # Added Course import

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    user_type = SelectField('Account Type', choices=[('student', 'Student'), ('faculty', 'Faculty')], validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class StudentProfileForm(FlaskForm):
    student_id = StringField('Student ID', validators=[DataRequired(), Length(min=3, max=20)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    department = StringField('Department', validators=[DataRequired(), Length(max=100)])
    year_of_study = IntegerField('Year of Study', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[Length(max=15), Optional()])
    submit = SubmitField('Save Profile')

    def validate_student_id(self, student_id):
        student = Student.query.filter_by(student_id=student_id.data).first()
        if student is not None:
            raise ValidationError('This Student ID is already registered.')

class FacultyProfileForm(FlaskForm):
    faculty_id = StringField('Faculty ID', validators=[DataRequired(), Length(min=3, max=20)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    department = StringField('Department', validators=[DataRequired(), Length(max=100)])
    position = StringField('Position', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone Number', validators=[Length(max=15), Optional()])
    submit = SubmitField('Save Profile')

    def validate_faculty_id(self, faculty_id):
        faculty = Faculty.query.filter_by(faculty_id=faculty_id.data).first()
        if faculty is not None:
            raise ValidationError('This Faculty ID is already registered.')

class CourseForm(FlaskForm):
    course_code = StringField('Course Code', validators=[DataRequired(), Length(max=20)])
    title = StringField('Course Title', validators=[DataRequired(), Length(max=100)])
    schedule = StringField('Schedule', validators=[DataRequired(), Length(max=200)])
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    min_attendance_percent = FloatField('Minimum Attendance (%)', default=75.0, validators=[DataRequired()])
    submit = SubmitField('Save Course')

class CourseSessionForm(FlaskForm):
    session_date = DateField('Session Date', validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])
    title = StringField('Session Title', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Session')

class AttendanceForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('present', 'Present'), 
        ('absent', 'Absent'), 
        ('late', 'Late'), 
        ('excused', 'Excused')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save')

class AbsenceRequestForm(FlaskForm):
    course_id = SelectField('Course', coerce=int, validators=[DataRequired()])
    from_date = DateField('From Date', validators=[DataRequired()])
    to_date = DateField('To Date', validators=[DataRequired()])
    from_time = TimeField('From Time', validators=[DataRequired()])
    to_time = TimeField('To Time', validators=[DataRequired()])
    reason = TextAreaField('Reason', validators=[DataRequired()])
    attachment = FileField('Attachment', validators=[Optional()])
    submit = SubmitField('Submit Request')

class AbsenceRequestResponseForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('approved', 'Approve'), 
        ('rejected', 'Reject')
    ], validators=[DataRequired()])
    response_notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Submit Response')

class TeacherAbsenceForm(FlaskForm):
    course_id = SelectField('Course', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    period = StringField('Period', validators=[DataRequired(), Length(max=50)])
    message = TextAreaField('Message for Students', validators=[DataRequired()])
    submit = SubmitField('Notify Students')