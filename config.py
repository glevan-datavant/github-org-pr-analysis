import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# GitHub API configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_URL = "https://api.github.com"
GITHUB_GRAPHQL_URL = f"{GITHUB_API_URL}/graphql"

# Organization settings
DEFAULT_ORG = os.getenv("GITHUB_ORG", "")

# API request settings
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds

# Concurrency settings
MAX_WORKERS = 5

# Output settings
OUTPUT_DIR = "output"
