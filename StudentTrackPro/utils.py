from datetime import datetime
from flask_mail import Message
from models import CourseEnrollment, Student, Course, CourseSession, Attendance, AttendanceNotification
from app import db, mail  # Ensure mail is imported

def send_attendance_notification(student_id, course_id, percentage):
    student = Student.query.get(student_id)
    course = Course.query.get(course_id)
    
    if not student or not course:
        return False
    
    subject = f"Attendance Warning: {course.title}"
    recipients = [student.user.email]
    
    body = f"""
    Dear {student.full_name},
    
    This is a notification regarding your attendance in {course.title} ({course.course_code}).
    
    Your current attendance percentage is {percentage:.2f}%, which is below the required minimum of {course.min_attendance_percent}% for this course.
    
    Please take necessary actions to improve your attendance. Contact your instructor {course.instructor.full_name} if you have any questions or need to discuss this matter.
    
    Best regards,
    Attendance System
    """
    
    msg = Message(subject=subject, recipients=recipients, body=body)
    
    try:
        mail.send(msg)
        # Record the notification
        notification = AttendanceNotification.query.filter_by(student_id=student_id, course_id=course_id).first()
        if not notification:
            notification = AttendanceNotification(student_id=student_id, course_id=course_id)
            db.session.add(notification)
        notification.notified_at = datetime.utcnow()
        notification.recovered = False  # Reset recovered status when notifying
        db.session.commit()
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def calculate_attendance(student_id, course_id, mail=None):
    course = Course.query.get(course_id)
    sessions = CourseSession.query.filter_by(course_id=course_id).all()
    
    attendance_records = db.session.query(Attendance).join(CourseSession).filter(
        Attendance.student_id == student_id,
        CourseSession.course_id == course_id
    ).all()
    
    total_sessions = len(sessions)
    if total_sessions == 0:
        return {
            'present': 0,
            'absent': 0,
            'late': 0,
            'excused': 0,
            'percentage': 0.0
        }
    
    present = sum(1 for r in attendance_records if r.status == 'present')
    absent = sum(1 for r in attendance_records if r.status == 'absent')
    late = sum(1 for r in attendance_records if r.status == 'late')
    excused = sum(1 for r in attendance_records if r.status == 'excused')
    
    attended_sessions = present + late
    percentage = (attended_sessions / total_sessions) * 100 if total_sessions > 0 else 0
    
    stats = {
        'present': present,
        'absent': absent,
        'late': late,
        'excused': excused,
        'percentage': percentage
    }
    
    if mail:
        notification = AttendanceNotification.query.filter_by(student_id=student_id, course_id=course_id).first()
        should_notify = False
        
        if percentage < course.min_attendance_percent:
            if not notification:  # Never notified before
                should_notify = True
            elif notification.recovered:  # Was above threshold, now below again
                should_notify = True
        elif percentage >= course.min_attendance_percent and notification and not notification.recovered:
            # Student recovered, mark as recovered but don't notify
            notification.recovered = True
            db.session.commit()
        
        if should_notify:
            success = send_attendance_notification(student_id, course_id, percentage)
            if not success:
                print(f"Failed to notify student {student_id} for course {course_id}")
    
    return stats

def get_attendance_stats(course_id):
    enrollments = db.session.query(CourseEnrollment).filter_by(course_id=course_id).all()
    below_threshold = 0
    
    for enrollment in enrollments:
        stats = calculate_attendance(enrollment.student_id, course_id, None)
        if stats['percentage'] < Course.query.get(course_id).min_attendance_percent:
            below_threshold += 1
    
    return {'below_threshold': below_threshold}