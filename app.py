import os
import re
import secrets
from datetime import date, datetime
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory,
    abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from config import Config, get_db_connection

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Regex pattern for email validation
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


# ---------------------------------------------------------------------------
# Security: CSRF Protection & Context Helpers
# ---------------------------------------------------------------------------
def generate_csrf_token():
    """Generates or retrieves a CSRF token stored in session."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(24)
    return session["_csrf_token"]


def verify_csrf_token():
    """Verifies that the submitted CSRF token matches the session token."""
    token = request.form.get("csrf_token")
    expected = session.get("_csrf_token")
    return bool(token and expected and secrets.compare_digest(token, expected))


@app.context_processor
def inject_template_globals():
    """Provides csrf_token and current_year to all Jinja2 templates."""
    return {
        "csrf_token": generate_csrf_token,
        "current_year": datetime.now().year,
    }


@app.before_request
def csrf_protect():
    """Validates CSRF token on state-modifying POST requests."""
    if request.method == "POST":
        # Allow resume upload or form POSTs to be verified
        if not verify_csrf_token():
            flash("Security check failed: Invalid or expired session form token. Please try again.", "error")
            return redirect(request.referrer or url_for("home"))


# ---------------------------------------------------------------------------
# Access Control Decorators
# ---------------------------------------------------------------------------
def student_required(f):
    """Ensures the authenticated user has student privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "student" or not session.get("user_id"):
            flash("Please sign in with your student account to access that page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Ensures the authenticated user has administrator privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "admin" or not session.get("admin_id"):
            flash("Administrator authentication required. Please sign in as an admin.", "warning")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    """Checks if the uploaded file extension is in the permitted set."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# Public Routes: Home, Jobs, Registration, Authentication
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    """Portal Landing Page with hero, live statistics, and featured drives."""
    stats = {
        "active_jobs": 0,
        "total_students": 0,
        "total_companies": 0,
        "selected_students": 0
    }
    recent_jobs = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Count active jobs
        cursor.execute("SELECT COUNT(*) AS count FROM jobs WHERE status = 'Active'")
        res = cursor.fetchone()
        stats["active_jobs"] = res["count"] if res else 0

        # Count registered students
        cursor.execute("SELECT COUNT(*) AS count FROM students")
        res = cursor.fetchone()
        stats["total_students"] = res["count"] if res else 0

        # Count unique hiring companies
        cursor.execute("SELECT COUNT(DISTINCT company_name) AS count FROM jobs")
        res = cursor.fetchone()
        stats["total_companies"] = res["count"] if res else 0

        # Count selected offers
        cursor.execute("SELECT COUNT(*) AS count FROM applications WHERE application_status = 'Selected'")
        res = cursor.fetchone()
        stats["selected_students"] = res["count"] if res else 0

        # Top 3 featured active job drives
        cursor.execute("""
            SELECT * FROM jobs
            WHERE status = 'Active' AND application_deadline >= CURRENT_DATE()
            ORDER BY created_at DESC LIMIT 3
        """)
        recent_jobs = cursor.fetchall()

        cursor.close()
        conn.close()
    except Exception as err:
        app.logger.error("Failed to load home page statistics: %s", err)

    return render_template("index.html", stats=stats, recent_jobs=recent_jobs)


@app.route("/jobs")
def jobs():
    """Searchable & Filterable Job Opportunities Directory."""
    query = request.args.get("q", "").strip()
    location = request.args.get("location", "").strip()
    skill = request.args.get("skill", "").strip()

    sql = "SELECT * FROM jobs WHERE status = 'Active'"
    params = []

    if query:
        sql += " AND (company_name LIKE %s OR job_title LIKE %s OR description LIKE %s)"
        like_q = f"%{query}%"
        params.extend([like_q, like_q, like_q])

    if location:
        sql += " AND location LIKE %s"
        params.append(f"%{location}%")

    if skill:
        sql += " AND required_skills LIKE %s"
        params.append(f"%{skill}%")

    sql += " ORDER BY created_at DESC"

    jobs_list = []
    applied_job_ids = set()

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, tuple(params))
        jobs_list = cursor.fetchall()

        # If student is logged in, mark jobs they've applied for
        if session.get("role") == "student" and session.get("user_id"):
            cursor.execute("SELECT job_id FROM applications WHERE student_id = %s", (session["user_id"],))
            applied_job_ids = {row["job_id"] for row in cursor.fetchall()}

        cursor.close()
        conn.close()
    except Exception as err:
        flash(f"Error loading job postings: {err}", "error")

    return render_template(
        "jobs.html",
        jobs=jobs_list,
        applied_job_ids=applied_job_ids,
        query=query,
        location=location,
        skill=skill
    )


@app.route("/jobs/<int:job_id>")
def job_details(job_id):
    """Detailed view of a single job opening."""
    job = None
    existing_application = None
    is_expired = False

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()

        if not job:
            cursor.close()
            conn.close()
            abort(404)

        if job["application_deadline"]:
            deadline_val = job["application_deadline"]
            if isinstance(deadline_val, datetime):
                deadline_val = deadline_val.date()
            is_expired = deadline_val < date.today()

        # Check existing student application
        if session.get("role") == "student" and session.get("user_id"):
            cursor.execute(
                "SELECT * FROM applications WHERE student_id = %s AND job_id = %s",
                (session["user_id"], job_id)
            )
            existing_application = cursor.fetchone()

        cursor.close()
        conn.close()
    except Exception as err:
        flash(f"Error retrieving job information: {err}", "error")

    if not job:
        abort(404)

    return render_template(
        "job_details.html",
        job=job,
        existing_application=existing_application,
        is_expired=is_expired
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    """Student Registration with client and server validation."""
    if session.get("role") == "student":
        return redirect(url_for("student_dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        college = request.form.get("college", "").strip()
        branch = request.form.get("branch", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        form_data = {
            "name": name,
            "email": email,
            "college": college,
            "branch": branch
        }

        # Server-side validation
        if not name or not email or not college or not branch or not password:
            flash("All required fields must be filled.", "error")
            return render_template("register.html", form_data=form_data)

        if not EMAIL_REGEX.match(email):
            flash("Please provide a valid email address.", "error")
            return render_template("register.html", form_data=form_data)

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return render_template("register.html", form_data=form_data)

        if password != confirm_password:
            flash("Passwords do not match. Please re-enter them carefully.", "error")
            return render_template("register.html", form_data=form_data)

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Check for duplicate email
            cursor.execute("SELECT id FROM students WHERE email = %s", (email,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                flash("An account with this email address already exists. Please log in.", "warning")
                return render_template("register.html", form_data=form_data)

            # Hash password securely
            password_hash = generate_password_hash(password)

            cursor.execute("""
                INSERT INTO students (full_name, email, college_name, department, password_hash)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, email, college, branch, password_hash))

            conn.commit()
            cursor.close()
            conn.close()

            flash("Account registered successfully! You can now log in.", "success")
            return redirect(url_for("login"))
        except Exception as err:
            flash(f"Registration failed: {err}", "error")
            return render_template("register.html", form_data=form_data)

    return render_template("register.html", form_data=None)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Student Login authentication."""
    if session.get("role") == "student":
        return redirect(url_for("student_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both your email address and password.", "error")
            return render_template("login.html", email=email)

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM students WHERE email = %s", (email,))
            student = cursor.fetchone()
            cursor.close()
            conn.close()

            if student and check_password_hash(student["password_hash"], password):
                # Successful login: setup session
                session.clear()
                session["user_id"] = student["id"]
                session["user_name"] = student["full_name"]
                session["user_email"] = student["email"]
                session["role"] = "student"

                flash(f"Welcome back, {student['full_name']}!", "success")
                return redirect(url_for("student_dashboard"))
            else:
                flash("Invalid email address or password. Please try again.", "error")
        except Exception as err:
            flash(f"Database error during sign-in: {err}", "error")

        return render_template("login.html", email=email)

    return render_template("login.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Administrator Login authentication."""
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both admin username and password.", "error")
            return render_template("admin_login.html", username=username)

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))
            admin = cursor.fetchone()
            cursor.close()
            conn.close()

            if admin and check_password_hash(admin["password_hash"], password):
                session.clear()
                session["admin_id"] = admin["id"]
                session["admin_username"] = admin["username"]
                session["role"] = "admin"

                flash(f"Welcome to Admin Portal, {admin['username']}!", "success")
                return redirect(url_for("admin_dashboard"))
            else:
                flash("Invalid admin username or password.", "error")
        except Exception as err:
            flash(f"Error during admin authentication: {err}", "error")

        return render_template("admin_login.html", username=username)

    return render_template("admin_login.html")


@app.route("/logout")
def logout():
    """Logs out student or admin and clears session."""
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# Student Routes: Dashboard, Applications, Profile, Apply
# ---------------------------------------------------------------------------
@app.route("/student/dashboard")
@student_required
def student_dashboard():
    """Student Dashboard with overview metrics and recent applications."""
    student_id = session["user_id"]
    stats = {"total_applied": 0, "pending": 0, "shortlisted": 0, "selected": 0}
    student = None
    recent_applications = []
    open_jobs = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Student details
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()

        # Status counts
        cursor.execute("""
            SELECT application_status, COUNT(*) AS count
            FROM applications
            WHERE student_id = %s
            GROUP BY application_status
        """, (student_id,))
        for row in cursor.fetchall():
            status_key = row["application_status"].lower()
            if status_key in stats:
                stats[status_key] = row["count"]
            stats["total_applied"] += row["count"]

        # Recent applications
        cursor.execute("""
            SELECT a.*, j.company_name, j.job_title
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.student_id = %s
            ORDER BY a.applied_at DESC LIMIT 5
        """, (student_id,))
        recent_applications = cursor.fetchall()

        # Recommended open jobs not yet applied to
        cursor.execute("""
            SELECT * FROM jobs
            WHERE status = 'Active'
              AND application_deadline >= CURRENT_DATE()
              AND id NOT IN (SELECT job_id FROM applications WHERE student_id = %s)
            ORDER BY created_at DESC LIMIT 3
        """, (student_id,))
        open_jobs = cursor.fetchall()

        cursor.close()
        conn.close()
    except Exception as err:
        flash(f"Error loading dashboard: {err}", "error")

    return render_template(
        "student_dashboard.html",
        student=student or {"full_name": session.get("user_name", "Student")},
        stats=stats,
        recent_applications=recent_applications,
        open_jobs=open_jobs
    )


@app.route("/student/applications")
@student_required
def student_applications():
    """Student view of all submitted job applications."""
    student_id = session["user_id"]
    applications = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, j.company_name, j.job_title, j.location, j.salary
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.student_id = %s
            ORDER BY a.applied_at DESC
        """, (student_id,))
        applications = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as err:
        flash(f"Error retrieving applications: {err}", "error")

    return render_template("applications.html", applications=applications)


@app.route("/student/profile", methods=["GET", "POST"])
@student_required
def student_profile():
    """Student profile view and update endpoint."""
    student_id = session["user_id"]

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_profile":
            full_name = request.form.get("full_name", "").strip()
            college_name = request.form.get("college_name", "").strip()
            department = request.form.get("department", "").strip()

            if not full_name or not college_name or not department:
                flash("All profile fields are required.", "error")
            else:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE students
                        SET full_name = %s, college_name = %s, department = %s
                        WHERE id = %s
                    """, (full_name, college_name, department, student_id))
                    conn.commit()
                    cursor.close()
                    conn.close()

                    session["user_name"] = full_name
                    flash("Your profile information has been updated successfully.", "success")
                except Exception as err:
                    flash(f"Failed to update profile: {err}", "error")

        elif action == "change_password":
            current_pw = request.form.get("current_password", "")
            new_pw = request.form.get("new_password", "")
            confirm_new_pw = request.form.get("confirm_new_password", "")

            if not current_pw or not new_pw:
                flash("Please complete all password fields.", "error")
            elif len(new_pw) < 8:
                flash("New password must be at least 8 characters long.", "error")
            elif new_pw != confirm_new_pw:
                flash("New password confirmation does not match.", "error")
            else:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT password_hash FROM students WHERE id = %s", (student_id,))
                    student = cursor.fetchone()

                    if student and check_password_hash(student["password_hash"], current_pw):
                        new_hash = generate_password_hash(new_pw)
                        cursor.execute("UPDATE students SET password_hash = %s WHERE id = %s", (new_hash, student_id))
                        conn.commit()
                        flash("Password updated successfully!", "success")
                    else:
                        flash("Current password was incorrect. Please try again.", "error")

                    cursor.close()
                    conn.close()
                except Exception as err:
                    flash(f"Password update failed: {err}", "error")

        return redirect(url_for("student_profile"))

    # GET request
    student = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as err:
        flash(f"Error loading profile: {err}", "error")

    if not student:
        flash("Student profile not found.", "error")
        return redirect(url_for("login"))

    return render_template("profile.html", student=student)


@app.route("/jobs/<int:job_id>/apply", methods=["POST"])
@student_required
def apply_job(job_id):
    """Handles student job application submission with resume file upload."""
    student_id = session["user_id"]
    cover_letter = request.form.get("cover_letter", "").strip()

    # Validate file upload
    if "resume" not in request.files:
        flash("Please select a resume file to upload.", "error")
        return redirect(url_for("job_details", job_id=job_id))

    file = request.files["resume"]
    if file.filename == "":
        flash("No file was selected for upload.", "error")
        return redirect(url_for("job_details", job_id=job_id))

    if not allowed_file(file.filename):
        flash("Invalid file format. Only PDF, DOC, and DOCX files are accepted.", "error")
        return redirect(url_for("job_details", job_id=job_id))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Verify job is active and deadline has not passed
        cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        if not job or job["status"] != "Active":
            cursor.close()
            conn.close()
            flash("This job drive is no longer active.", "error")
            return redirect(url_for("jobs"))

        deadline = job["application_deadline"]
        if isinstance(deadline, datetime):
            deadline = deadline.date()
        if deadline < date.today():
            cursor.close()
            conn.close()
            flash("The application deadline for this drive has already passed.", "error")
            return redirect(url_for("job_details", job_id=job_id))

        # Check duplicate application
        cursor.execute(
            "SELECT id FROM applications WHERE student_id = %s AND job_id = %s",
            (student_id, job_id)
        )
        if cursor.fetchone():
            cursor.close()
            conn.close()
            flash("You have already submitted an application for this position.", "warning")
            return redirect(url_for("job_details", job_id=job_id))

        # Save resume safely
        original_name = secure_filename(file.filename)
        timestamp = int(datetime.now().timestamp())
        unique_filename = f"resume_{student_id}_{job_id}_{timestamp}_{original_name}"
        save_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        file.save(save_path)

        # Insert application into database
        cursor.execute("""
            INSERT INTO applications (student_id, job_id, resume_filename, cover_letter, application_status)
            VALUES (%s, %s, %s, %s, 'Pending')
        """, (student_id, job_id, unique_filename, cover_letter))

        conn.commit()
        cursor.close()
        conn.close()

        flash(f"Application submitted successfully for {job['job_title']} at {job['company_name']}!", "success")
        return redirect(url_for("student_applications"))
    except Exception as err:
        flash(f"Failed to submit application: {err}", "error")
        return redirect(url_for("job_details", job_id=job_id))


# ---------------------------------------------------------------------------
# Admin Routes: Dashboard, Job Management, Applications Review, Students
# ---------------------------------------------------------------------------
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Administrator Dashboard with platform metrics and recent activity."""
    stats = {
        "total_students": 0,
        "total_jobs": 0,
        "active_jobs": 0,
        "total_applications": 0,
        "selected_count": 0
    }
    recent_applications = []
    recent_jobs = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Metric counts
        cursor.execute("SELECT COUNT(*) AS count FROM students")
        stats["total_students"] = (cursor.fetchone() or {})["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM jobs")
        stats["total_jobs"] = (cursor.fetchone() or {})["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM jobs WHERE status = 'Active'")
        stats["active_jobs"] = (cursor.fetchone() or {})["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM applications")
        stats["total_applications"] = (cursor.fetchone() or {})["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM applications WHERE application_status = 'Selected'")
        stats["selected_count"] = (cursor.fetchone() or {})["count"]

        # Recent 5 applications
        cursor.execute("""
            SELECT a.*, s.full_name AS student_name, s.email AS student_email,
                   s.college_name, s.department, j.company_name, j.job_title
            FROM applications a
            JOIN students s ON a.student_id = s.id
            JOIN jobs j ON a.job_id = j.id
            ORDER BY a.applied_at DESC LIMIT 5
        """)
        recent_applications = cursor.fetchall()

        # Recent jobs with applicant count
        cursor.execute("""
            SELECT j.*, COUNT(a.id) AS application_count
            FROM jobs j
            LEFT JOIN applications a ON j.id = a.job_id
            GROUP BY j.id
            ORDER BY j.created_at DESC LIMIT 5
        """)
        recent_jobs = cursor.fetchall()

        cursor.close()
        conn.close()
    except Exception as err:
        flash(f"Error loading admin dashboard: {err}", "error")

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        recent_applications=recent_applications,
        recent_jobs=recent_jobs
    )


@app.route("/admin/jobs")
@admin_required
def manage_jobs():
    """View and manage all job postings."""
    jobs_list = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT j.*, COUNT(a.id) AS application_count
            FROM jobs j
            LEFT JOIN applications a ON j.id = a.job_id
            GROUP BY j.id
            ORDER BY j.created_at DESC
        """)
        jobs_list = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as err:
        flash(f"Error loading jobs: {err}", "error")

    return render_template("manage_jobs.html", jobs=jobs_list, edit_job=None)


@app.route("/admin/jobs/new", methods=["POST"])
@admin_required
def create_job():
    """Creates a new job posting."""
    company_name = request.form.get("company_name", "").strip()
    job_title = request.form.get("job_title", "").strip()
    description = request.form.get("description", "").strip()
    required_skills = request.form.get("required_skills", "").strip()
    eligibility = request.form.get("eligibility", "").strip()
    location = request.form.get("location", "").strip()
    salary = request.form.get("salary", "").strip() or None
    deadline_str = request.form.get("application_deadline", "").strip()
    status = request.form.get("status", "Active")

    if not company_name or not job_title or not description or not required_skills or not eligibility or not location or not deadline_str:
        flash("Please complete all required job information fields.", "error")
        return redirect(url_for("manage_jobs"))

    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid deadline date format. Please use YYYY-MM-DD.", "error")
        return redirect(url_for("manage_jobs"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jobs (company_name, job_title, description, required_skills,
                              eligibility, location, salary, application_deadline, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (company_name, job_title, description, required_skills, eligibility, location, salary, deadline, status))
        conn.commit()
        cursor.close()
        conn.close()

        flash(f"New job drive '{job_title}' at '{company_name}' published successfully!", "success")
    except Exception as err:
        flash(f"Failed to create job posting: {err}", "error")

    return redirect(url_for("manage_jobs"))


@app.route("/admin/jobs/<int:job_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_job(job_id):
    """Edits an existing job posting."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        job_title = request.form.get("job_title", "").strip()
        description = request.form.get("description", "").strip()
        required_skills = request.form.get("required_skills", "").strip()
        eligibility = request.form.get("eligibility", "").strip()
        location = request.form.get("location", "").strip()
        salary = request.form.get("salary", "").strip() or None
        deadline_str = request.form.get("application_deadline", "").strip()
        status = request.form.get("status", "Active")

        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
            cursor.execute("""
                UPDATE jobs
                SET company_name = %s, job_title = %s, description = %s,
                    required_skills = %s, eligibility = %s, location = %s,
                    salary = %s, application_deadline = %s, status = %s
                WHERE id = %s
            """, (company_name, job_title, description, required_skills,
                  eligibility, location, salary, deadline, status, job_id))
            conn.commit()
            flash("Job posting updated successfully.", "success")
            cursor.close()
            conn.close()
            return redirect(url_for("manage_jobs"))
        except Exception as err:
            flash(f"Failed to update job: {err}", "error")

    # GET: Pre-populate edit form
    cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
    edit_job_obj = cursor.fetchone()

    cursor.execute("""
        SELECT j.*, COUNT(a.id) AS application_count
        FROM jobs j
        LEFT JOIN applications a ON j.id = a.job_id
        GROUP BY j.id
        ORDER BY j.created_at DESC
    """)
    jobs_list = cursor.fetchall()

    cursor.close()
    conn.close()

    if not edit_job_obj:
        abort(404)

    return render_template("manage_jobs.html", jobs=jobs_list, edit_job=edit_job_obj)


@app.route("/admin/jobs/<int:job_id>/toggle-status", methods=["POST"])
@admin_required
def toggle_job_status(job_id):
    """Toggles job status between Active and Inactive."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT status FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()

        if job:
            new_status = "Inactive" if job["status"] == "Active" else "Active"
            cursor.execute("UPDATE jobs SET status = %s WHERE id = %s", (new_status, job_id))
            conn.commit()
            flash(f"Job drive status changed to {new_status}.", "info")

        cursor.close()
        conn.close()
    except Exception as err:
        flash(f"Error toggling job status: {err}", "error")

    return redirect(url_for("manage_jobs"))


@app.route("/admin/jobs/<int:job_id>/delete", methods=["POST"])
@admin_required
def delete_job(job_id):
    """Permanently deletes a job posting and cascades application removal."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Job drive deleted successfully.", "success")
    except Exception as err:
        flash(f"Failed to delete job: {err}", "error")

    return redirect(url_for("manage_jobs"))


@app.route("/admin/applications")
@admin_required
def admin_applications():
    """Review, search, and filter all student candidate applications."""
    selected_job_id = request.args.get("job_id", "").strip()
    selected_status = request.args.get("status", "").strip()
    query = request.args.get("q", "").strip()

    sql = """
        SELECT a.*, s.full_name AS student_name, s.email AS student_email,
               s.college_name, s.department, j.company_name, j.job_title
        FROM applications a
        JOIN students s ON a.student_id = s.id
        JOIN jobs j ON a.job_id = j.id
        WHERE 1=1
    """
    params = []

    if selected_job_id:
        sql += " AND a.job_id = %s"
        params.append(selected_job_id)

    if selected_status:
        sql += " AND a.application_status = %s"
        params.append(selected_status)

    if query:
        sql += " AND (s.full_name LIKE %s OR s.email LIKE %s)"
        params.extend([f"%{query}%", f"%{query}%"])

    sql += " ORDER BY a.applied_at DESC"

    applications = []
    all_jobs = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, tuple(params))
        applications = cursor.fetchall()

        cursor.execute("SELECT id, company_name, job_title FROM jobs ORDER BY company_name ASC")
        all_jobs = cursor.fetchall()

        cursor.close()
        conn.close()
    except Exception as err:
        flash(f"Error retrieving applications: {err}", "error")

    return render_template(
        "manage_applications.html",
        applications=applications,
        all_jobs=all_jobs,
        selected_job_id=selected_job_id,
        selected_status=selected_status,
        query=query
    )


@app.route("/admin/applications/<int:app_id>/status", methods=["POST"])
@admin_required
def update_application_status(app_id):
    """Updates candidate application status."""
    new_status = request.form.get("status", "").strip()
    valid_statuses = {"Pending", "Shortlisted", "Selected", "Rejected"}

    if new_status not in valid_statuses:
        flash("Invalid application status selected.", "error")
        return redirect(request.referrer or url_for("admin_applications"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE applications SET application_status = %s WHERE id = %s",
            (new_status, app_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash(f"Candidate status updated to '{new_status}'.", "success")
    except Exception as err:
        flash(f"Error updating status: {err}", "error")

    return redirect(request.referrer or url_for("admin_applications"))


@app.route("/admin/students")
@admin_required
def admin_students():
    """Directory of all registered students."""
    query = request.args.get("q", "").strip()
    dept = request.args.get("dept", "").strip()

    sql = """
        SELECT s.*, COUNT(a.id) AS applications_count
        FROM students s
        LEFT JOIN applications a ON s.id = a.student_id
        WHERE 1=1
    """
    params = []

    if query:
        sql += " AND (s.full_name LIKE %s OR s.email LIKE %s OR s.college_name LIKE %s)"
        like_q = f"%{query}%"
        params.extend([like_q, like_q, like_q])

    if dept:
        sql += " AND s.department LIKE %s"
        params.append(f"%{dept}%")

    sql += " GROUP BY s.id ORDER BY s.created_at DESC"

    students_list = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, tuple(params))
        students_list = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as err:
        flash(f"Error loading student directory: {err}", "error")

    return render_template(
        "manage_students.html",
        students=students_list,
        query=query,
        dept=dept
    )


# ---------------------------------------------------------------------------
# File Management: Secure Resume Access
# ---------------------------------------------------------------------------
@app.route("/resumes/<path:filename>")
def view_resume(filename):
    """
    Secure resume file access.
    Allowed only for:
    1. Authenticated Administrators.
    2. The candidate student who submitted the resume.
    """
    # Authorization check
    is_admin = session.get("role") == "admin"
    student_id = session.get("user_id")

    if not is_admin and not student_id:
        flash("You must be logged in to view resumes.", "warning")
        return redirect(url_for("login"))

    if not is_admin:
        # Check student ownership of this resume file
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id FROM applications WHERE student_id = %s AND resume_filename = %s",
                (student_id, filename)
            )
            owned = cursor.fetchone()
            cursor.close()
            conn.close()

            if not owned:
                abort(403)
        except Exception:
            abort(403)

    return send_from_directory(Config.UPLOAD_FOLDER, filename)


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    """Custom 404 Not Found error page."""
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    """Custom 500 Internal Server error page."""
    return render_template("500.html"), 500


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    """Handles uploads exceeding the 5MB limit."""
    flash("Uploaded file exceeds the maximum permitted size of 5MB.", "error")
    return redirect(request.referrer or url_for("home"))


# ---------------------------------------------------------------------------
# Administrative Setup Command Line Helper
# ---------------------------------------------------------------------------
def create_admin_account(username, password):
    """Helper function to create or reset an administrator account with hashed password."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        password_hash = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO admins (username, password_hash)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash)
        """, (username, password_hash))

        conn.commit()
        cursor.close()
        conn.close()
        print(f"Success: Admin account '{username}' configured successfully!")
        return True
    except Exception as e:
        print(f"Error creating admin account: {e}")
        return False


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "create-admin":
        user = sys.argv[2] if len(sys.argv) > 2 else "admin"
        pw = sys.argv[3] if len(sys.argv) > 3 else "Admin@12345"
        create_admin_account(user, pw)
    else:
        # Run local development server
        app.run(host="127.0.0.1", port=5000, debug=True)
