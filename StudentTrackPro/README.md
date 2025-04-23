# StudentTrackPro 📚

## Project Overview

StudentTrackPro is a comprehensive attendance and absence management system for educational institutions. It enables students and faculty to manage attendance, absence requests, notifications, and course information through a user-friendly web interface. The system supports secure authentication, file uploads for absence documentation, automated email notifications, and detailed reporting for administrators and faculty.

## Key Features

- **User Authentication**: Secure login, registration, and profile management for students and faculty
- **Student Dashboard**: View courses, attendance statistics, recent absences, and notifications
- **Faculty Dashboard**: Manage courses, sessions, student enrollments, and attendance
- **Attendance Management**: Take, view, and report attendance for each session
- **Absence Requests**: Students can submit absence requests with documentation; faculty can review and respond
- **Teacher Absence Notification**: Faculty can notify students of class cancellations with automated email alerts
- **File Uploads**: Students can attach documentation to absence requests
- **Automated Email Notifications**: Email alerts for class cancellations and absence request responses
- **Reporting**: Attendance analytics and reports for faculty
- **Role-Based Access**: Separate dashboards and permissions for students and faculty

## Technology Stack

- **Backend**: Python with Flask framework
- **Database**: SQLAlchemy (supports SQLite/PostgreSQL)
- **Frontend**: HTML, CSS, JavaScript with Bootstrap (via Flask templates)
- **Email**: Flask-Mail with SMTP for notifications
- **File Uploads**: Secure file handling with Werkzeug
- **Authentication**: Flask-Login

## Project Structure

```
StudentTrackPro/
├── app.py                      # Main application entry point and configuration
├── routes.py                   # Application routes and logic (student, faculty, attendance, etc.)
├── models.py                   # Database models (User, Student, Faculty, Course, etc.)
├── forms.py                    # WTForms definitions for all forms
├── utils.py                    # Utility functions (attendance calculation, notifications, etc.)
├── requirements.txt            # Python dependencies
├── static/                     # Static files (CSS, JS, images)
├── templates/                  # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── student/
│   │   ├── dashboard.html
│   │   ├── view_attendance.html
│   │   └── absence_request.html
│   ├── faculty/
│   │   ├── dashboard.html
│   │   ├── course_management.html
│   │   ├── student_management.html
│   │   ├── take_attendance.html
│   │   ├── absence_requests.html
│   │   ├── notify_absence.html
│   │   └── reports.html
│   └── ... (other templates)
├── uploads/                    # Uploaded files (absence documentation)
├── README.md                   # This file
└── ... (other scripts and files)
```

## Installation & Setup

### Prerequisites

- Python 3.8+
- (Optional) PostgreSQL for production
- (Optional) wkhtmltopdf for PDF export (if implemented)

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/StudentTrackPro.git
   cd StudentTrackPro
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory with the following variables:
   ```
   DATABASE_URL=sqlite:///studenttrackpro.db
   SECRET_KEY=your-secret-key-here
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-email-password
   ```

5. **Initialize the database:**
   ```bash
   flask shell
   >>> from app import db
   >>> db.create_all()
   >>> exit()
   ```

6. **Run the application:**
   ```bash
   python app.py
   ```
   Access the application at [http://localhost:5000](http://localhost:5000)

## Key Application Routes

### Authentication & Profiles
- `/login` - User login
- `/register` - User registration
- `/logout` - Logout
- `/update_profile` - Update student/faculty profile

### Student
- `/student/dashboard` - Student dashboard
- `/student/view_attendance/<course_id>` - View attendance for a course
- `/student/absence_request` - Submit absence request
- `/student/absence_requests` - View submitted absence requests

### Faculty
- `/faculty/dashboard` - Faculty dashboard
- `/faculty/course_management` - Manage courses
- `/faculty/edit_course/<course_id>` - Edit course details
- `/faculty/delete_course/<course_id>` - Delete a course
- `/faculty/course/<course_id>/sessions` - Manage course sessions
- `/faculty/student_management/<course_id>` - Manage student enrollments
- `/faculty/enroll_student` - Enroll a student in a course
- `/faculty/remove_enrollment/<enrollment_id>` - Remove a student from a course
- `/faculty/take_attendance/<session_id>` - Take attendance for a session
- `/faculty/absence_requests` - View and respond to student absence requests
- `/faculty/respond_absence_request/<request_id>` - Respond to an absence request
- `/faculty/notify_absence` - Notify students of faculty absence
- `/faculty/reports` - Attendance reports

### API
- `/api/course_report/<course_id>` - Get attendance report data for a course

### File Handling
- `/download_attachment/<request_id>` - Download absence request documentation

## Configuration Options

Key configuration options in `app.py`:

```python
# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///studenttrackpro.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Secret key for sessions
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

# Email configuration
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
)

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
```

## System Components

### Attendance & Absence Management

- **Attendance Calculation**: Automated attendance percentage and status calculation for each student and course
- **Absence Requests**: Students submit requests with optional documentation; faculty can approve/deny and automatically update attendance records
- **Notifications**: Email notifications for class cancellations and absence request responses

### Reporting

- **Faculty Reports**: Attendance analytics per course and session, students below attendance threshold

### Security

- **Role-Based Access**: Separate dashboards and permissions for students and faculty
- **File Upload Security**: Secure handling of uploaded files

## Development & Contribution

- Use feature branches for new features or bug fixes.
- Use `git status` and `git add` to stage only the files you want to commit.

## Deployment

For production deployment:

1. Set up a PostgreSQL database (optional)
2. Configure a production-ready WSGI server (Gunicorn, uWSGI)
3. Set up a reverse proxy (Nginx, Apache)
4. Configure production email settings
5. Set `DEBUG=False` in production

## License

For any questions or support, please contact the development team.
