-- ==========================================================
-- Smart Campus Placement Management System
-- Database Schema & Initial Seed Data
-- ==========================================================

CREATE DATABASE IF NOT EXISTS smart_campus_placement
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE smart_campus_placement;

-- ----------------------------------------------------------
-- 1. Students Table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    college_name VARCHAR(150) NOT NULL,
    department VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_student_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- 2. Administrators Table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_admin_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- 3. Job Openings Table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(150) NOT NULL,
    job_title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    required_skills VARCHAR(255) NOT NULL,
    eligibility VARCHAR(255) NOT NULL,
    location VARCHAR(120) NOT NULL,
    salary VARCHAR(100) DEFAULT NULL,
    application_deadline DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    INDEX idx_job_status (status),
    INDEX idx_job_deadline (application_deadline)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- 4. Job Applications Table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    job_id INT NOT NULL,
    resume_filename VARCHAR(255) NOT NULL,
    cover_letter TEXT DEFAULT NULL,
    application_status ENUM('Pending', 'Shortlisted', 'Selected', 'Rejected') DEFAULT 'Pending',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_application_student FOREIGN KEY (student_id)
        REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT fk_application_job FOREIGN KEY (job_id)
        REFERENCES jobs(id) ON DELETE CASCADE,
    CONSTRAINT uk_student_job UNIQUE (student_id, job_id),
    INDEX idx_application_status (application_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- Seed Initial Demo Administrator
-- Username: admin
-- Default Password: Admin@12345
-- ----------------------------------------------------------
INSERT INTO admins (username, password_hash)
VALUES (
    'admin',
    'scrypt:32768:8:1$8zAEOU7jZEHPZYUj$5b8bbf0d98b345d47bd8259363321cc44445ec3ac7644d486b51a92700cc0031d943a214a5e0cc0831642df3f13364369c559f7abf974a22d5f7aa74344b687d'
)
ON DUPLICATE KEY UPDATE username=username;

-- ----------------------------------------------------------
-- Seed Realistic Sample Job Opportunities (Demo Data)
-- ----------------------------------------------------------
INSERT INTO jobs (company_name, job_title, description, required_skills, eligibility, location, salary, application_deadline, status)
VALUES
(
    'Apex Cloud Systems',
    'Graduate Software Engineer (Python / Flask)',
    'Join our cloud engineering team to design, develop, and maintain high-performance microservices and RESTful APIs using Python, Flask, and relational databases. You will collaborate with cross-functional teams in an agile environment and participate in code reviews.',
    'Python, Flask, MySQL, REST APIs, Git',
    'B.Tech / B.E in CS, IT, or ECE with min 65% aggregate or 6.5 CGPA',
    'Bangalore, Karnataka',
    '₹6.5 - ₹8.5 LPA',
    DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY),
    'Active'
),
(
    'NexGen Digital Labs',
    'Frontend Developer Trainee',
    'We are seeking an enthusiastic frontend developer skilled in modern HTML5, CSS3, JavaScript, and responsive UI design. You will build user-friendly interfaces, dashboards, and responsive web portals for enterprise clients worldwide.',
    'HTML5, CSS3, JavaScript (ES6+), Bootstrap/Tailwind, Responsive Design',
    'B.Tech, BCA, MCA, or B.Sc Computer Science graduates with strong portfolio',
    'Hyderabad, Telangana',
    '₹5.0 - ₹6.8 LPA',
    DATE_ADD(CURRENT_DATE, INTERVAL 40 DAY),
    'Active'
),
(
    'InfraMetrics Analytics',
    'Associate Data Analyst',
    'Work alongside senior analytics professionals to clean, transform, and analyze placement and operational datasets. Create insightful visualizations and dashboards to support business decision-making.',
    'SQL, Python (Pandas/NumPy), Excel, PowerBI / Tableau',
    'Open to all engineering and mathematics/statistics graduates with 60%+ aggregate',
    'Pune, Maharashtra',
    '₹5.5 - ₹7.2 LPA',
    DATE_ADD(CURRENT_DATE, INTERVAL 25 DAY),
    'Active'
),
(
    'Q-Matrix Technologies',
    'Quality Assurance & Automation Engineer',
    'Exciting opportunity for entry-level candidates interested in software testing and quality automation. Responsibilities include writing test cases, performing regression testing, and creating automated scripts using Python and Selenium.',
    'Manual Testing, Selenium, Python, Test Automation, Bug Reporting',
    'B.E / B.Tech in CS, IT, EEE, ECE with no active backlogs',
    'Chennai, Tamil Nadu',
    '₹4.5 - ₹5.8 LPA',
    DATE_ADD(CURRENT_DATE, INTERVAL 20 DAY),
    'Active'
),
(
    'StratoSphere Networks',
    'Junior Cloud & DevOps Associate',
    'Help us deploy and scale cloud-native applications on AWS and Docker. You will learn CI/CD pipelines, container management, and infrastructure monitoring in a supportive team environment.',
    'Linux Fundamentals, Docker, AWS Basics, Python/Bash Scripting',
    'B.Tech in CS/IT/ECE or MCA with strong operating systems foundation',
    'Remote (India)',
    '₹7.0 - ₹9.0 LPA',
    DATE_ADD(CURRENT_DATE, INTERVAL 45 DAY),
    'Active'
)
ON DUPLICATE KEY UPDATE id=id;

