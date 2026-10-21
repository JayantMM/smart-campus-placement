
import os
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "smart_placement_super_secret_dev_key_2026"
    )

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "smart_campus_placement")

    # Optional path to the Aiven CA certificate
    DB_SSL_CA = os.getenv(
        "DB_SSL_CA",
        str(BASE_DIR / "ca.pem")
    )

    UPLOAD_FOLDER = os.path.join(
        BASE_DIR,
        os.getenv("UPLOAD_FOLDER", "uploads/resumes")
    )
    MAX_CONTENT_LENGTH = int(
        os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024)
    )
    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}


os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)


def get_db_connection():
    try:
        options = {
            "host": Config.DB_HOST,
            "port": Config.DB_PORT,
            "user": Config.DB_USER,
            "password": Config.DB_PASSWORD,
            "database": Config.DB_NAME,
            "charset": "utf8mb4",
            "autocommit": False,
        }

        # Use and verify Aiven's CA certificate when available
        if Config.DB_HOST != "localhost" and os.path.isfile(
            Config.DB_SSL_CA
        ):
            options["ssl_ca"] = Config.DB_SSL_CA
            options["ssl_verify_cert"] = True
            options["ssl_verify_identity"] = True

        return mysql.connector.connect(**options)

    except (Error, ValueError) as err:
        raise RuntimeError(
            f"MySQL connection failed at "
            f"{Config.DB_HOST}:{Config.DB_PORT}, "
            f"database '{Config.DB_NAME}'. Details: {err}"
        ) from err
