# 🎓 Smart Campus Placement Management System

A full-stack, responsive, and secure **Smart Campus Placement Management System** built with **Python Flask**, **MySQL**, **HTML5**, **CSS3**, and **JavaScript**.

Designed specifically for college campus recruitment drives, allowing students to discover jobs, upload resumes, and track their selection status while giving placement coordinators full administrative oversight.

---

## 🌟 Key Features

### For Students
- **Candidate Registration & Login:** Safe authentication using Werkzeug password hashing.
- **Searchable Job Openings:** Filter by keyword, company name, location, and required technical skills.
- **Job Details & Deadlines:** Full role overview, package details, eligibility criteria, and deadline tracking.
- **Easy Online Application:** Secure resume upload (PDF/DOC/DOCX, up to 5MB) with optional cover letter.
- **Application Tracking:** Track application stages in real-time (`Pending`, `Shortlisted`, `Selected`, `Rejected`).
- **Profile Management:** Update academic information, college, branch, and change account passwords.

### For Placement Officers & Administrators
- **Executive Dashboard:** Live metrics for total students, active job postings, total applications, and placed students.
- **Job Posting Management:** Create, update, toggle status (`Active` / `Inactive`), or remove job postings.
- **Candidate Screening:** Screen candidate applications by job and status, view cover letters, and download submitted resumes.
- **Application Status Updates:** Update candidate stages directly with immediate feedback.
- **Student Directory:** Search and browse registered students and view their total application count.

### Security & Robustness
- **Password Protection:** Passwords securely hashed with `werkzeug.security` (scrypt / pbkdf2:sha256). Plaintext passwords are never saved.
- **SQL Injection Prevention:** All database operations utilize parameterized queries with `mysql-connector-python`.
- **Session & CSRF Protection:** Cryptographic CSRF tokens embedded in all forms and validated on every state-changing POST request.
- **Secure File Storage:** Unique filename generation with timestamps and extension whitelisting (`.pdf`, `.doc`, `.docx`).
- **Access Control:** Role-based decorators (`@student_required`, `@admin_required`) protect student and admin sections.

---

## 📁 Project Architecture

```text
smart campus placement/
│
├── app.py                     # Main Flask application, routes & business logic
├── config.py                  # Database & environment configuration
├── init_admin.py              # Command-line utility to initialize/reset admin account
├── test_app.py                # Automated integration test suite
├── requirements.txt           # Python dependencies
├── README.md                  # Complete documentation and setup guide
├── .env                       # Local environment variables
├── .env.example               # Template environment configuration
├── .gitignore                 # Git ignore rules for virtualenv, uploads, etc.
│
├── templates/                 # Jinja2 HTML Templates
│   ├── base.html              # Shared responsive navigation, alerts & footer
│   ├── index.html             # Homepage with hero, statistics & feature cards
│   ├── register.html          # Student registration form with validation
│   ├── login.html             # Student login form
│   ├── admin_login.html       # Administrator portal login
│   ├── jobs.html              # Searchable and filterable job listings
│   ├── job_details.html       # Detailed drive specifications & application form
│   ├── student_dashboard.html # Student dashboard with status cards & recent applications
│   ├── admin_dashboard.html   # Admin dashboard with system metrics & quick actions
│   ├── applications.html      # Student's submitted applications view
│   ├── admin_applications.html# Admin application screening & status updates
│   ├── admin_students.html    # Admin student candidate directory
│   ├── profile.html           # Student profile & password settings
│   ├── manage_jobs.html       # Admin job creation & management interface
│   ├── 404.html               # Custom 404 Not Found error page
│   └── 500.html               # Custom 500 Server Error page
│
├── static/
│   ├── css/
│   │   └── style.css          # Modern dark-blue & white responsive stylesheet
│   ├── js/
│   │   └── script.js          # Interactive UI scripts (navigation, alerts, file preview)
│   └── images/                # Static image assets
│
├── database/
│   └── schema.sql             # MySQL schema with tables & sample demo jobs
│
├── uploads/
│   └── resumes/               # Secure directory storing uploaded student resumes
│
└── .venv/                     # Python 3.14 virtual environment
```

---

## 🚀 Getting Started (Beginner-Friendly Windows Setup)

Follow these steps to run the project in **VS Code on Windows**:

### Step 1: Start MySQL in XAMPP
1. Open the **XAMPP Control Panel** on your computer.
2. In the **MySQL** row, click the **Start** button.
3. Confirm that the status background turns green and port `3306` is displayed.

> **Note on XAMPP Defaults:** By default, XAMPP uses username `root` with no password (`""`), which matches the project's default `.env` configuration.

---

### Step 2: Import the Database Schema
Open **PowerShell** in the project folder (`D:\smart campus placement`) and run:

```powershell
C:\xampp\mysql\bin\mysql.exe -u root -e "source D:/smart campus placement/database/schema.sql"
```

*Alternatively, you can open **phpMyAdmin** in your browser (`http://localhost/phpmyadmin`), click **Import**, select `database/schema.sql`, and click **Go**.*

This command creates the database `smart_campus_placement`, initializes all 4 tables (`students`, `admins`, `jobs`, `applications`), and loads realistic demo job listings.

---

### Step 3: Activate the Virtual Environment & Verify Dependencies

In your VS Code terminal (PowerShell), activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

If you ever need to install or update dependencies:

```powershell
pip install -r requirements.txt
```

---

### Step 4: Initialize the Admin Account

Run the administrator initialization script from your project directory:

python init_admin.py

For security, configure a unique administrator username and password. Do not use default or publicly shared credentials.

To provide custom credentials, use:

python init_admin.py <your_username> <your_password>

Keep administrator credentials private and never commit them to the public repository.

---

### Step 5: Start the Flask Application

Run:

```powershell
python app.py
```

You will see:
```text
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

Open your browser and navigate to:

👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🧪 Testing Checklist

You can verify all major features using the automated test suite or through the browser:

### Option A: Run Automated Tests
In your terminal, execute:

```powershell
python test_app.py
```

This tests 100% of all public routes, static CSS/JS delivery, student registration, login, resume uploads, duplicate prevention, and admin workflows automatically.

---

### Option B: Manual Browser Testing

| Feature | Steps to Test | Expected Outcome |
| :--- | :--- | :--- |
| **1. Home Page** | Visit `http://127.0.0.1:5000` | Displays hero section, database statistics, feature cards, and latest jobs. |
| **2. Search Jobs** | Click **Jobs** in navbar, enter "Python" in keyword search | Filters active jobs matching the query in real-time. |
| **3. Student Registration** | Click **Register**, fill in details, submit | Account is created, password is securely hashed, redirects to Login. |
| **4. Student Login** | Login with your registered email and password | Redirects to Student Dashboard with personalized greeting and statistics. |
| **5. Job Application** | Navigate to a job detail page, upload a PDF resume, click **Submit Application** | Application is saved, status set to "Pending", redirects to My Applications. |
| **6. Prevent Duplicate** | Return to the same job detail page | Shows "Your Application Status: Pending" and hides the application form. |
| **7. Admin Login** | Click **Login** &rarr; **Admin Login** (or visit `/admin/login`), enter `admin` / `Admin@12345` | Accesses Administrator Dashboard with full system metrics. |
| **8. Status Update** | Go to **Applications**, change candidate status to `Shortlisted`, click **Save** | Status changes to Shortlisted with instant green badge. |
| **9. Post New Job** | In Admin, go to **Manage Jobs**, fill form, click **Publish** | New job drive becomes immediately visible on public Jobs page. |
| **10. Responsive UI** | Resize your browser window to mobile width | Mobile hamburger toggle menu appears and operates smoothly. |

---

## 🛠️ Configuration Settings

Application configuration is stored in `.env`. Key settings:

```ini
# Flask secret key for sessions
SECRET_KEY=smart_placement_super_secret_dev_key_2026

# MySQL Database credentials
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=smart_campus_placement

# File upload limits (5MB)
MAX_CONTENT_LENGTH=5242880
UPLOAD_FOLDER=uploads/resumes
```

---

## ❓ Troubleshooting & Common Questions

### 1. PowerShell Script Execution Error
If running `.\.venv\Scripts\Activate.ps1` gives `running scripts is disabled on this system`, run this once in PowerShell:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
Then run `.\.venv\Scripts\Activate.ps1` again.

### 2. Can't Connect to MySQL Server (10061)
- Verify the **MySQL** module is started in the **XAMPP Control Panel**.
- Test connection manually:
  ```powershell
  C:\xampp\mysql\bin\mysql.exe -u root
  ```
- If your local root account uses a password, set `DB_PASSWORD=your_password` in `.env`.

### 3. Port 5000 is Busy / Already in Use
You can run Flask on another port by running:
```powershell
python -m flask run --port 5001
```
And access it at `http://127.0.0.1:5001`.

### 4. Reset Admin Account
If you forget the admin credentials, reset them instantly:
```powershell
python init_admin.py admin Admin@12345
```

---

## 📋 Completed Deliverables Summary

- [x] Corrected folder structure and removed misplaced files from `.venv`.
- [x] Responsive dark-blue and crisp white UI theme in `static/css/style.css` (no 404 static errors).
- [x] Complete MySQL relational database schema in `database/schema.sql`.
- [x] Student registration, login, logout, and profile management with Werkzeug password hashing.
- [x] Job search, keyword filtering, and detail views.
- [x] Resume upload with size/type validation and duplicate application prevention.
- [x] Student dashboard with live application tracking (`Pending`, `Shortlisted`, `Selected`, `Rejected`).
- [x] Protected Admin area with drive creation, editing, status toggling, and applicant screening.
- [x] Secure admin initialization utility (`init_admin.py`).
- [x] CSRF protection and custom 404/500 error pages.
- [x] Full automated integration test suite (`test_app.py`).
- [x] Incomplete features: None. All requirements from the specification are fully implemented.

