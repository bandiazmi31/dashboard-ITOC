import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Core Flask settings
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
    SESSION_TYPE = "filesystem"
    PERMANENT_SESSION_LIFETIME = int(os.getenv("SESSION_TIMEOUT", "30")) * 60  # seconds

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ManageEngine API
    TECHNICIAN_KEY = os.getenv("TECHNICIAN_KEY")
    MANAGEENGINE_BASE_URL = "http://helpdesk.pelindomultiterminal.co.id:8080/api/v3"

    # Misc
    DEBUG = True
