import os
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

# Load environment variables from .env file if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Application configuration loaded from environment variables."""
    SECRET_KEY = os.getenv("SECRET_KEY", "smart_placement_super_secret_dev_key_2026")

    # MySQL database configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "smart_campus_placement")

    # Uploads configuration
    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.getenv("UPLOAD_FOLDER", "uploads/resumes"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))  # 5 MB
    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}


# Ensure upload directory exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)


def get_db_connection():
    """
    Creates and returns a MySQL database connection.
    Raises RuntimeError with friendly instructions if the connection fails.
    """
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset="utf8mb4",
            autocommit=False
        )
        return connection
    except Error as err:
        error_msg = (
            f"Failed to connect to MySQL database '{Config.DB_NAME}' at {Config.DB_HOST}:{Config.DB_PORT}.\n"
            f"Details: {err}\n"
            "Please make sure:\n"
            "1. MySQL is running in your XAMPP Control Panel.\n"
            "2. The database 'smart_campus_placement' exists (run database/schema.sql).\n"
            "3. Your database credentials in .env are correct."
        )
        raise RuntimeError(error_msg) from err

