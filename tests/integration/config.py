"""
Configuration for integration tests.
"""

import os

# Service URLs
ML_BASE_URL = os.getenv("ML_BASE_URL", "http://localhost:8000")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")

# Test configuration
DEFAULT_TIMEOUT = 30
RETRY_COUNT = 3
RETRY_DELAY = 1
