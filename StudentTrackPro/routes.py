from flask_mail import Message
from app import db, mail, app  # Add app for file upload configuration
from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from sqlalchemy import func
from datetime import datetime, date
from models import TeacherAbsenceNotification, User, Student, Faculty, Course, CourseEnrollment, CourseSession, Attendance, AbsenceRequest
from forms import LoginForm, RegistrationForm, StudentProfileForm, FacultyProfileForm, CourseForm, CourseSessionForm, AttendanceForm, AbsenceRequestForm, AbsenceRequestResponseForm,TeacherAbsenceForm
from utils import calculate_attendance, get_attendance_stats, send_attendance_notification
import os
from werkzeug.utils import secure_filename

def register_routes(app):
    # Ensure uploads directory exists
    UPLOAD_FOLDER = 'uploads'
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Authentication routes
    @app.route('/')
    @app.route('/index')
    def index():
        if current_user.is_authenticated:
            if current_user.user_type == 'student':
                return redirect(url_for('student_dashboard'))
            else:
                return redirect(url_for('faculty_dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.check_password(form.password.data):
                flash('Invalid username or password', 'danger')
                return redirect(url_for('login'))
            
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
        
        return render_template('login.html', title='Sign In', form=form)

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, email=form.email.data, user_type=form.user_type.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            
            flash('Congratulations, you are now registered! Please complete your profile.', 'success')
            login_user(user)
            
            if user.user_type == 'student':
                return redirect(url_for('create_student_profile'))
            else:
                return redirect(url_for('create_faculty_profile'))
                
        return render_template('register.html', title='Register', form=form)

    # Profile creation routes
    @app.route('/create_student_profile', methods=['GET', 'POST'])
    @login_required
    def create_student_profile():
        if current_user.user_type != 'student':
            flash('Access denied: You are not registered as a student', 'danger')
            return redirect(url_for('index'))
        
        if Student.query.filter_by(user_id=current_user.id).first():
            flash('You already have a student profile', 'info')
            return redirect(url_for('student_dashboard'))
        
        form = StudentProfileForm()
        if form.validate_on_submit():
            student = Student(
                user_id=current_user.id,
                student_id=form.student_id.data,
                full_name=form.full_name.data,
                department=form.department.data,
                year_of_study=form.year_of_study.data,
                phone=form.phone.data
            )
            db.session.add(student)
            db.session.commit()
            flash('Your student profile has been created!', 'success')
            return redirect(url_for('student_dashboard'))
            
        return render_template('register.html', title='Create Student Profile', form=form)

    @app.route('/create_faculty_profile', methods=['GET', 'POST'])
    @login_required
    def create_faculty_profile():
        if current_user.user_type != 'faculty':
            flash('Access denied: You are not registered as faculty', 'danger')
            return redirect(url_for('index'))
        
        if Faculty.query.filter_by(user_id=current_user.id).first():
            flash('You already have a faculty profile', 'info')
            return redirect(url_for('faculty_dashboard'))
        
        form = FacultyProfileForm()
        if form.validate_on_submit():
            faculty = Faculty(
                user_id=current_user.id,
                faculty_id=form.faculty_id.data,
                full_name=form.full_name.data,
                department=form.department.data,
                position=form.position.data,
                phone=form.phone.data
            )
            db.session.add(faculty)
            db.session.commit()
            flash('Your faculty profile has been created!', 'success')
            return redirect(url_for('faculty_dashboard'))
            
        return render_template('register.html', title='Create Faculty Profile', form=form)

    # Student routes
    @app.route('/student/dashboard')
    @login_required
    def student_dashboard():
        if current_user.user_type != 'student':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            return redirect(url_for('create_student_profile'))
        
        enrollments = CourseEnrollment.query.filter_by(student_id=student.id).all()
        courses = [enrollment.course for enrollment in enrollments]
        
        attendance_stats = {}
        for course in courses:
            attendance_stats[course.id] = calculate_attendance(student.id, course.id)
            
        recent_absences = Attendance.query.join(CourseSession).join(Course)\
            .filter(Attendance.student_id == student.id)\
            .filter(Attendance.status == 'absent')\
            .order_by(CourseSession.session_date.desc())\
            .limit(5).all()
            
        pending_requests = AbsenceRequest.query.filter_by(
            student_id=student.id, status='pending'
        ).order_by(AbsenceRequest.from_date.desc()).all()
        
        # Fetch absence notifications for the student
        absence_notifications = TeacherAbsenceNotification.query.join(Course).join(CourseEnrollment)\
            .filter(CourseEnrollment.student_id == student.id)\
            .order_by(TeacherAbsenceNotification.notified_at.desc()).all()
        
        return render_template('student/dashboard.html', 
                            student=student,
                            courses=courses,
                            attendance_stats=attendance_stats,
                            recent_absences=recent_absences,
                            pending_requests=pending_requests,
                            absence_notifications=absence_notifications)
    @app.route('/student/view_attendance/<int:course_id>')
    @login_required
    def student_view_attendance(course_id):
        if current_user.user_type != 'student':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            return redirect(url_for('create_student_profile'))
        
        course = Course.query.get_or_404(course_id)
        
        # Check if student is enrolled in this course
        enrollment = CourseEnrollment.query.filter_by(
            student_id=student.id, course_id=course_id
        ).first()
        if not enrollment:
            flash('You are not enrolled in this course', 'danger')
            return redirect(url_for('student_dashboard'))
        
        attendance_records = db.session.query(
            CourseSession, Attendance
        ).outerjoin(
            Attendance, (CourseSession.id == Attendance.session_id) & 
                       (Attendance.student_id == student.id)
        ).filter(
            CourseSession.course_id == course_id
        ).order_by(
            CourseSession.session_date
        ).all()
        
        stats = calculate_attendance(student.id, course_id)
        
        return render_template('student/view_attendance.html',
                              student=student,
                              course=course,
                              attendance_records=attendance_records,
                              stats=stats)

    @app.route('/student/absence_request', methods=['GET', 'POST'])
    @login_required
    def create_absence_request():
        if current_user.user_type != 'student':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            return redirect(url_for('create_student_profile'))
        
        form = AbsenceRequestForm()
        
        # Populate the course choices
        enrollments = CourseEnrollment.query.filter_by(student_id=student.id).all()
        form.course_id.choices = [(enrollment.course_id, enrollment.course.title) for enrollment in enrollments]
        
        if form.validate_on_submit():
            if form.from_date.data > form.to_date.data:
                flash('The end date cannot be before the start date', 'danger')
                return render_template('student/absence_request.html', form=form)
                
            request = AbsenceRequest(
                student_id=student.id,
                course_id=form.course_id.data,
                request_date=date.today(),
                from_date=form.from_date.data,
                to_date=form.to_date.data,
                from_time=form.from_time.data,
                to_time=form.to_time.data,
                reason=form.reason.data,
                status='pending'
            )
            
            # Handle file upload
            if form.attachment.data:
                file = form.attachment.data
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                request.documentation = filename  # Use 'documentation' field instead of 'attachment'
            
            db.session.add(request)
            db.session.commit()
            flash('Your absence request has been submitted', 'success')
            return redirect(url_for('student_dashboard'))
            
        return render_template('student/absence_request.html', form=form)

    @app.route('/student/absence_requests')
    @login_required
    def view_absence_requests():
        if current_user.user_type != 'student':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            return redirect(url_for('create_student_profile'))
        
        requests = AbsenceRequest.query.filter_by(student_id=student.id).order_by(
            AbsenceRequest.request_date.desc()
        ).all()
        
        return render_template('student/absence_request.html',
                              requests=requests,
                              view_only=True)

    @app.route('/faculty/dashboard')
    @login_required
    def faculty_dashboard():
        if current_user.user_type != 'faculty':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        faculty = Faculty.query.filter_by(user_id=current_user.id).first()
        if not faculty:
            return redirect(url_for('create_faculty_profile'))
        
        courses = Course.query.filter_by(faculty_id=faculty.id).all()
        
        today = date.today()
        today_sessions = CourseSession.query.join(Course).filter(
            Course.faculty_id == faculty.id,
            CourseSession.session_date == today
        ).order_by(CourseSession.start_time).all()
        
        pending_requests = AbsenceRequest.query.join(Course).filter(
            Course.faculty_id == faculty.id,
            AbsenceRequest.status == 'pending'
        ).count()
        
        course_stats = {}
        for course in courses:
            stats = get_attendance_stats(course.id)
            course_stats[course.id] = stats
        
        # Fix: Use dictionary key access instead of attribute access
        no_actions_needed = pending_requests == 0 and not any(course_stats[course.id]['below_threshold'] > 0 for course in courses)
        
        return render_template('faculty/dashboard.html',
                            faculty=faculty,
                            courses=courses,
                            today_sessions=today_sessions,
                            pending_requests=pending_requests,
                            course_stats=course_stats,
                            no_actions_needed=no_actions_needed)

    @app.route('/faculty/course_management', methods=['GET', 'POST'])
    @login_required
    def course_management():
        if current_user.user_type != 'faculty':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        faculty = Faculty.query.filter_by(user_id=current_user.id).first()
        if not faculty:
            return redirect(url_for('create_faculty_profile'))
        
        form = CourseForm()
        
        if form.validate_on_submit():
            course = Course(
                course_code=form.course_code.data,
                title=form.title.data,
                faculty_id=faculty.id,
                schedule=form.schedule.data,
                location=form.location.data,
                description=form.description.data,
                min_attendance_percent=form.min_attendance_percent.data
            )
            db.session.add(course)
            db.session.commit()
            flash('Course has been created!', 'success')
            return redirect(url_for('course_management'))
        
        courses = Course.query.filter_by(faculty_id=faculty.id).all()
        
        return render_template('faculty/course_management.html',
                              form=form,
                              courses=courses)

    @app.route('/faculty/edit_course/<int:course_id>', methods=['GET', 'POST'])
    @login_required
    def edit_course(course_id):
        if current_user.user_type != 'faculty':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        faculty = Faculty.query.filter_by(user_id=current_user.id).first()
        course = Course.query.get_or_404(course_id)
        
        if course.faculty_id != faculty.id:
            flash('You do not have permission to edit this course', 'danger')
            return redirect(url_for('course_management'))
        
        form = CourseForm(obj=course)
        
        if form.validate_on_submit():
            form.populate_obj(course)
            db.session.commit()
            flash('Course has been updated!', 'success')
            return redirect(url_for('course_management'))
        
        return render_template('faculty/course_management.html',
                              form=form,
                              edit_mode=True,
                              course=course)

    @app.route('/faculty/delete_course/<int:course_id>', methods=['POST'])
    @login_required
    def delete_course(course_id):
        if current_user.user_type != 'faculty':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        faculty = Faculty.query.filter_by(user_id=current_user.id).first()
        course = Course.query.get_or_404(course_id)
        
        if course.faculty_id != faculty.id:
            flash('You do not have permission to delete this course', 'danger')
            return redirect(url_for('course_management'))
        
        db.session.delete(course)
        db.session.commit()
        flash('Course has been deleted!', 'success')
        return redirect(url_for('course_management'))

    @app.route('/faculty/course/<int:course_id>/sessions', methods=['GET', 'POST'])
    @login_required
    def course_sessions(course_id):
        if current_user.user_type != 'faculty':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        faculty = Faculty.query.filter_by(user_id=current_user.id).first()
        course = Course.query.get_or_404(course_id)
        
        if course.faculty_id != faculty.id:
            flash('You do not have permission to manage this course', 'danger')
            return redirect(url_for('course_management'))
        
        form = CourseSessionForm()
        
        if form.validate_on_submit():
            session = CourseSession(
                course_id=course.id,
                session_date=form.session_date.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data,
                title=form.title.data,
                notes=form.notes.data
            )
            db.session.add(session)
            db.session.commit()
            flash('Session has been added!', 'success')
            return redirect(url_for('course_sessions', course_id=course.id))
        
        sessions = CourseSession.query.filter_by(course_id=course.id).order_by(CourseSession.session_date, CourseSession.start_time).all()
        
        # Check attendance status for each session
        for session in sessions:
            session.attendance_taken = Attendance.query.filter_by(session_id=session.id).count() > 0
        
        today = date.today()
        
        return render_template('faculty/course_management.html',
                            form=form,
                            course=course,
                            sessions=sessions,
                            sessions_view=True,
                            today=today)

    @app.route('/faculty/student_management/<int:course_id>', methods=['GET'])
    @login_required
    def student_management(course_id):
        if current_user.user_type != 'faculty':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        faculty = Faculty.query.filter_by(user_id=current_user.id).first()
        course = Course.query.get_or_404(course_id)
        
        if course.faculty_id != faculty.id:
            flash('You do not have permission to manage this course', 'danger')
            return redirect(url_for('course_management'))
        
        enrollments = CourseEnrollment.query.filter_by(course_id=course.id).all()
        students = [enrollment.student for enrollment in enrollments]
        
        # Get all students that are not enrolled in this course
        all_students = Student.query.all()
        available_students = [s for s in all_students if s not in students]
        
        return render_template('faculty/student_management.html',
                              course=course,
                              enrollments=enrollments,
                              available_students=available_students)

    @app.route('/faculty/enroll_student', methods=['POST'])
    @login_required
    def enroll_student():
        if current_user.user_type != 'faculty':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        faculty = Faculty.query.filter_by(user_id=current_user.id).first()
        
        student_id = request.form.get('student_id')
        course_id = request.form.get('course_id')
        
        student = Student.query.get(student_id)
        course = Course.query.get(course_id)
        
        if not student or not course:
            flash('Invalid student or course', 'danger')
            return redirect(url_for('faculty_dashboard'))
        
        if course.faculty_id != faculty.id:
            flash('You do not have permission to manage this course', 'danger')
            return redirect(url_for('faculty_dashboard'))
        
        # Check if student is already enrolled
        existing = CourseEnrollment.query.filter_by(
            student_id=student.id, course_id=course.id
        ).first()
        
        if existing:
            flash(f'Student {student.full_name} is already enrolled in this course', 'warning')
        else:
            enrollment = CourseEnrollment(
                student_id=student.id,
                course_id=course.id
            )
            db.session.add(enrollment)
            db.session.commit()
            flash(f'Student {student.full_name} has been enrolled in {course.title}', 'success')
        
        return redirect(url_for('student_management', course_id=course.id))

    @app.route('/faculty/remove_enrollment/<int:enrollment_id>', methods=['POST'])
    @login_required
    def remove_enrollment(enrollment_id):
        if current_user.user_type != 'faculty':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        faculty = Faculty.query.filter_by(user_id=current_user.id).first()
        
        enrollment = CourseEnrollment.query.get_or_404(enrollment_id)
        course = Course.query.get(enrollment.course_id)
        
        if course.faculty_id != faculty.id:
            flash('You do not have permission to manage this course', 'danger')
            return redirect(url_for('faculty_dashboard'))
        
        student = Student.query.get(enrollment.student_id)
        course_id = course.id
        
        db.session.delete(enrollment)
        db.session.commit()
        
        flash(f'Student {student.full_name} has been removed from {course.title}', 'success')
        return redirect(url_for('student_management', course_id=course_id))

    @app.route('/faculty/take_attendance/<int:session_id>', methods=['GET', 'POST'])
    @login_required
    def take_attendance(session_id):
        if current_user.user_type != 'faculty':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        faculty = Faculty.query.filter_by(user_id=current_user.id).first()
        session = CourseSession.query.get_or_404(session_id)
        course = Course.query.get(session.course_id)
        
        if course.faculty_id != faculty.id:
            flash('You do not have permission to manage this course', 'danger')
            return redirect(url_for('faculty_dashboard'))
        
        enrollments = CourseEnrollment.query.filter_by(course_id=course.id).all()
        students = [enrollment.student for enrollment in enrollments]
        
        existing_records = {record.student_id: record for record in Attendance.query.filter_by(session_id=session.id).all()}
        
        if request.method == 'POST':
            for student in students:
                status = request.form.get(f'status_{student.id}')
                notes = request.form.get(f'notes_{student.id}', '')
                
                if student.id in existing_records:
                    record = existing_records[student.id]
                    record.status = status
                    record.notes = notes
                else:
                    record = Attendance(
                        student_id=student.id,
                        session_id=session.id,
                        status=status,
                        notes=notes
                    )
                    db.session.add(record)
            
            db.session.commit()
            
            # Check attendance and send notifications if needed
            for student in students:
                calculate_attendance(student.id, course.id, mail)  # Pass mail object
            
            flash('Attendance has been recorded successfully', 'success')
            return redirect(url_for('course_sessions', course_id=course.id))
        
        return render_template('faculty/take_attendance.html',
                            session=session,
                            course=course,
                            students=students,
                            existing_records=existing_records)
    
    @app.route('/faculty/absence_requests', methods=['GET'])
    @login_required
    def faculty_absence_requests():
        if current_user.user_type != 'faculty':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        faculty = Faculty.query.filter_by(user_id=current_user.id).first()
        
        # Get absence requests for courses taught by this faculty
        requests = AbsenceRequest.query.join(Course).filter(
            Course.faculty_id == faculty.id
        ).order_by(
            AbsenceRequest.status == 'pending',
            AbsenceRequest.request_date.desc()
        ).all()
        
        return render_template('faculty/absence_requests.html',
                              requests=requests)

    @app.route('/faculty/respond_absence_request/<int:request_id>', methods=['GET', 'POST'])
    @login_required
    def respond_absence_request(request_id):
        if current_user.user_type != 'faculty':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        faculty = Faculty.query.filter_by(user_id=current_user.id).first()
        
        absence_request = AbsenceRequest.query.get_or_404(request_id)
        course = Course.query.get(absence_request.course_id)
        
        if course.faculty_id != faculty.id:
            flash('You do not have permission to respond to this request', 'danger')
            return redirect(url_for('faculty_absence_requests'))
        
        form = AbsenceRequestResponseForm()
        
        if form.validate_on_submit():
            absence_request.status = form.status.data
            absence_request.response_notes = form.response_notes.data
            absence_request.responded_at = datetime.utcnow()
            
            # If approved, update attendance records to "excused" for the days in the request range
            if form.status.data == 'approved':
                from_date = absence_request.from_date
                to_date = absence_request.to_date
                
                # Find sessions in this date range
                sessions = CourseSession.query.filter(
                    CourseSession.course_id == course.id,
                    CourseSession.session_date >= from_date,
                    CourseSession.session_date <= to_date
                ).all()
                
                for session in sessions:
                    # Check if attendance record exists
                    attendance = Attendance.query.filter_by(
                        student_id=absence_request.student_id,
                        session_id=session.id
                    ).first()
                    
                    if attendance:
                        attendance.status = 'excused'
                        attendance.notes = f"Excused absence: {absence_request.reason}"
                    else:
                        # Create new attendance record with excused status
                        attendance = Attendance(
                            student_id=absence_request.student_id,
                            session_id=session.id,
                            status='excused',
                            notes=f"Excused absence: {absence_request.reason}"
                        )
                        db.session.add(attendance)
            
            db.session.commit()
            flash('Response to absence request has been submitted', 'success')
            return redirect(url_for('faculty_absence_requests'))
        
        student = Student.query.get(absence_request.student_id)
        
        return render_template('faculty/absence_requests.html',
                              form=form,
                              request=absence_request,
                              student=student,
                              course=course,
                              responding=True)

    @app.route('/faculty/reports', methods=['GET'])
    @login_required
    def attendance_reports():
        if current_user.user_type != 'faculty':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        
        faculty = Faculty.query.filter_by(user_id=current_user.id).first()
        courses = Course.query.filter_by(faculty_id=faculty.id).all()
        
        # Get data for course selection
        course_data = []
        for course in courses:
            enrollments = CourseEnrollment.query.filter_by(course_id=course.id).count()
            sessions = CourseSession.query.filter_by(course_id=course.id).count()
            course_data.append({
                'id': course.id,
                'title': course.title,
                'code': course.course_code,
                'students': enrollments,
                'sessions': sessions
            })
        
        return render_template('faculty/reports.html',
                              courses=course_data)

    @app.route('/api/course_report/<int:course_id>', methods=['GET'])
    @login_required
    def api_course_report(course_id):
        if current_user.user_type != 'faculty':
            return jsonify({'error': 'Access denied'}), 403
        
        faculty = Faculty.query.filter_by(user_id=current_user.id).first()
        course = Course.query.get_or_404(course_id)
        
        if course.faculty_id != faculty.id:
            return jsonify({'error': 'You do not have permission to view this course'}), 403
        
        enrollments = CourseEnrollment.query.filter_by(course_id=course.id).all()
        sessions = CourseSession.query.filter_by(course_id=course.id).all()
        
        # Calculate overall statistics
        total_sessions = len(sessions)
        student_data = []
        
        total_present = 0
        total_absent = 0
        total_late = 0
        total_excused = 0
        
        for enrollment in enrollments:
            student = Student.query.get(enrollment.student_id)
            stats = calculate_attendance(student.id, course.id)
            
            # Track overall stats
            total_present += stats['present']
            total_absent += stats['absent']
            total_late += stats['late']
            total_excused += stats['excused']
            
            student_data.append({
                'student_id': student.student_id,
                'name': student.full_name,
                'present': stats['present'],
                'absent': stats['absent'],
                'late': stats['late'],
                'excused': stats['excused'],
                'percentage': stats['percentage'],
                'below_threshold': stats['percentage'] < course.min_attendance_percent
            })
        
        # Sort students by attendance percentage (ascending)
        student_data.sort(key=lambda x: x['percentage'])
        
        # Calculate session statistics
        session_data = []
        for s in sessions:
            present_count = Attendance.query.filter_by(session_id=s.id, status='present').count()
            absent_count = Attendance.query.filter_by(session_id=s.id, status='absent').count()
            late_count = Attendance.query.filter_by(session_id=s.id, status='late').count()
            excused_count = Attendance.query.filter_by(session_id=s.id, status='excused').count()
            total_count = present_count + absent_count + late_count + excused_count
            
            if total_count > 0:
                attendance_rate = (present_count + late_count) / total_count * 100
            else:
                attendance_rate = 0
                
            session_data.append({
                'date': s.session_date.strftime('%Y-%m-%d'),
                'title': s.title or f"Session on {s.session_date.strftime('%b %d')}",
                'present': present_count,
                'absent': absent_count,
                'late': late_count,
                'excused': excused_count,
                'attendance_rate': attendance_rate
            })
        
        # Get students below threshold
        students_below_threshold = [s for s in student_data if s['below_threshold']]
        
        # Calculate overall attendance rate
        total_attendance = total_present + total_absent + total_late + total_excused
        if total_attendance > 0:
            overall_attendance_rate = (total_present + total_late) / total_attendance * 100
        else:
            overall_attendance_rate = 0
        
        return jsonify({
            'course': {
                'id': course.id,
                'code': course.course_code,
                'title': course.title,
                'min_attendance': course.min_attendance_percent
            },
            'summary': {
                'total_students': len(enrollments),
                'total_sessions': total_sessions,
                'overall_attendance_rate': overall_attendance_rate,
                'students_below_threshold': len(students_below_threshold)
            },
            'students': student_data,
            'sessions': session_data
        })

    # Common routes
    @app.route('/update_profile', methods=['GET', 'POST'])
    @login_required
    def update_profile():
        if current_user.user_type == 'student':
            student = Student.query.filter_by(user_id=current_user.id).first()
            if not student:
                return redirect(url_for('create_student_profile'))
                
            form = StudentProfileForm(obj=student)
            
            if form.validate_on_submit():
                # Skip validation of student_id if unchanged
                if form.student_id.data == student.student_id:
                    student.full_name = form.full_name.data
                    student.department = form.department.data
                    student.year_of_study = form.year_of_study.data
                    student.phone = form.phone.data
                else:
                    form.populate_obj(student)
                
                db.session.commit()
                flash('Your profile has been updated!', 'success')
                return redirect(url_for('student_dashboard'))
                
            return render_template('register.html', 
                                  title='Update Profile', 
                                  form=form, 
                                  edit_mode=True)
        else:
            faculty = Faculty.query.filter_by(user_id=current_user.id).first()
            if not faculty:
                return redirect(url_for('create_faculty_profile'))
                
            form = FacultyProfileForm(obj=faculty)
            
            if form.validate_on_submit():
                # Skip validation of faculty_id if unchanged
                if form.faculty_id.data == faculty.faculty_id:
                    faculty.full_name = form.full_name.data
                    faculty.department = form.department.data
                    faculty.position = form.position.data
                    faculty.phone = form.phone.data
                else:
                    form.populate_obj(faculty)
                
                db.session.commit()
                flash('Your profile has been updated!', 'success')
                return redirect(url_for('faculty_dashboard'))
                
            return render_template('register.html', 
                                  title='Update Profile', 
                                  form=form, 
                                  edit_mode=True)

    @app.route('/download_attachment/<int:request_id>')
    @login_required
    def download_attachment(request_id):
        request = AbsenceRequest.query.get_or_404(request_id)
        if request.documentation:
            return send_from_directory(app.config['UPLOAD_FOLDER'], request.documentation)
        flash('No attachment available', 'warning')
        return redirect(url_for('view_absence_requests'))
@app.route('/faculty/notify_absence', methods=['GET', 'POST'])
@login_required
def notify_absence():
    if current_user.user_type != 'faculty':
        flash('Access denied', 'danger')
        return redirect(url_for('index'))
    
    faculty = Faculty.query.filter_by(user_id=current_user.id).first()
    if not faculty:
        return redirect(url_for('create_faculty_profile'))
    
    form = TeacherAbsenceForm()
    form.course_id.choices = [(course.id, course.title) for course in faculty.courses]
    
    if form.validate_on_submit():
        notification = TeacherAbsenceNotification(
            faculty_id=faculty.id,
            course_id=form.course_id.data,
            date=form.date.data,
            period=form.period.data,
            message=form.message.data
        )
        db.session.add(notification)
        db.session.commit()

        # Notify enrolled students
        course = Course.query.get(form.course_id.data)
        enrollments = CourseEnrollment.query.filter_by(course_id=course.id).all()
        for enrollment in enrollments:
            student = enrollment.student
            subject = f"Class Cancellation: {course.title} on {form.date.data}"
            body = f"""
            Dear {student.full_name},
            
            I will not be able to attend the {form.period.data} class for {course.title} on {form.date.data}.
            Please use this time to work on: {form.message.data}.
            
            Best regards,
            {faculty.full_name}
            """
            msg = Message(subject=subject, recipients=[student.user.email], body=body)
            try:
                mail.send(msg)
            except Exception as e:
                print(f"Failed to send email: {str(e)}")
        flash('Students have been notified of your absence', 'success')
        return redirect(url_for('faculty_dashboard'))
    
    return render_template('faculty/notify_absence.html', form=form)    