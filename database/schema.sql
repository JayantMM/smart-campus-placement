-- ==========================================================
-- Smart Campus Placement Management System
-- Aiven MySQL Database Schema
-- Database: defaultdb
-- ==========================================================

USE defaultdb;

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
    application_status ENUM(
        'Pending',
        'Shortlisted',
        'Selected',
        'Rejected'
    ) DEFAULT 'Pending',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_application_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_application_job
        FOREIGN KEY (job_id)
        REFERENCES jobs(id)
        ON DELETE CASCADE,

    CONSTRAINT uk_student_job
        UNIQUE (student_id, job_id),

    INDEX idx_application_status (application_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- 5. Demo Administrator
-- Inserts only if username 'admin' does not already exist.
-- ----------------------------------------------------------
INSERT INTO admins (username, password_hash)
VALUES (
    'admin',
    'scrypt:32768:8:1$8zAEOU7jZEHPZYUj$5b8bbf0d98b345d47bd8259363321cc44445ec3ac7644d486b51a92700cc0031d943a214a5e0cc0831642df3f13364369c559f7abf974a22d5f7aa74344b687d'
)
ON DUPLICATE KEY UPDATE username = username;

-- ----------------------------------------------------------
-- 6. Sample Job Openings
-- Insert each demo job only if its company and title
-- combination does not already exist.
-- ----------------------------------------------------------

INSERT INTO jobs (
    company_name,
    job_title,
    description,
    required_skills,
    eligibility,
    location,
    salary,
    application_deadline,
    status
)
SELECT
    'Apex Cloud Systems',
    'Graduate Software Engineer (Python / Flask)',
    'Join our cloud engineering team to develop and maintain applications and REST APIs using Python, Flask, and relational databases.',
    'Python, Flask, MySQL, REST APIs, Git',
    'B.Tech / B.E in CS, IT, or ECE with minimum 65% aggregate or 6.5 CGPA',
    'Bangalore, Karnataka',
    '₹6.5 - ₹8.5 LPA',
    DATE_ADD(CURRENT_DATE, INTERVAL 30 DAY),
    'Active'
WHERE NOT EXISTS (
    SELECT 1 FROM jobs
    WHERE company_name = 'Apex Cloud Systems'
      AND job_title = 'Graduate Software Engineer (Python / Flask)'
);

INSERT INTO jobs (
    company_name, job_title, description, required_skills,
    eligibility, location, salary, application_deadline, status
)
SELECT
    'NexGen Digital Labs',
    'Frontend Developer Trainee',
    'Build responsive web interfaces and dashboards using HTML, CSS, and JavaScript.',
    'HTML5, CSS3, JavaScript, Responsive Design',
    'B.Tech, BCA, MCA, or B.Sc Computer Science graduates',
    'Hyderabad, Telangana',
    '₹5.0 - ₹6.8 LPA',
    DATE_ADD(CURRENT_DATE, INTERVAL 40 DAY),
    'Active'
WHERE NOT EXISTS (
    SELECT 1 FROM jobs
    WHERE company_name = 'NexGen Digital Labs'
      AND job_title = 'Frontend Developer Trainee'
);

INSERT INTO jobs (
    company_name, job_title, description, required_skills,
    eligibility, location, salary, application_deadline, status
)
SELECT
    'InfraMetrics Analytics',
    'Associate Data Analyst',
    'Clean, transform, and analyze datasets and create visualizations to support business decisions.',
    'SQL, Python, Pandas, NumPy, Excel, Power BI',
    'Graduates in computer science, engineering, mathematics, or statistics with 60%+ aggregate',
    'Pune, Maharashtra',
    '₹5.5 - ₹7.2 LPA',
    DATE_ADD(CURRENT_DATE, INTERVAL 25 DAY),
    'Active'
WHERE NOT EXISTS (
    SELECT 1 FROM jobs
    WHERE company_name = 'InfraMetrics Analytics'
      AND job_title = 'Associate Data Analyst'
);

INSERT INTO jobs (
    company_name, job_title, description, required_skills,
    eligibility, location, salary, application_deadline, status
)
SELECT
    'Q-Matrix Technologies',
    'Quality Assurance & Automation Engineer',
    'Write test cases, perform regression testing, and create automation scripts.',
    'Manual Testing, Selenium, Python, Test Automation',
    'B.E / B.Tech in CS, IT, EEE, or ECE with no active backlogs',
    'Chennai, Tamil Nadu',
    '₹4.5 - ₹5.8 LPA',
    DATE_ADD(CURRENT_DATE, INTERVAL 20 DAY),
    'Active'
WHERE NOT EXISTS (
    SELECT 1 FROM jobs
    WHERE company_name = 'Q-Matrix Technologies'
      AND job_title = 'Quality Assurance & Automation Engineer'
);

INSERT INTO jobs (
    company_name, job_title, description, required_skills,
    eligibility, location, salary, application_deadline, status
)
SELECT
    'StratoSphere Networks',
    'Junior Cloud & DevOps Associate',
    'Assist with deploying and monitoring cloud applications, containers, and CI/CD pipelines.',
    'Linux, Docker, AWS Basics, Python, Bash',
    'B.Tech in CS/IT/ECE or MCA with a strong operating systems foundation',
    'Remote (India)',
    '₹7.0 - ₹9.0 LPA',
    DATE_ADD(CURRENT_DATE, INTERVAL 45 DAY),
    'Active'
WHERE NOT EXISTS (
    SELECT 1 FROM jobs
    WHERE company_name = 'StratoSphere Networks'
      AND job_title = 'Junior Cloud & DevOps Associate'
);

-- ----------------------------------------------------------
-- 7. Verify the tables and sample jobs
-- ----------------------------------------------------------
SHOW TABLES;

SELECT id, company_name, job_title, status, application_deadline
FROM jobs
ORDER BY id;