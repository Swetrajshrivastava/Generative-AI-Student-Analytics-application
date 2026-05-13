import os
from dotenv import load_dotenv

# Load environment variables from the workspace root .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Change this when deploying
API_URL = os.getenv(
    "API_URL",
    "http://localhost:8000"
)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "student-analytics-admin-token")
