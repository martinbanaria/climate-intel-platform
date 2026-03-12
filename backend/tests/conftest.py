"""
Shared pytest fixtures for Climate Intel backend tests.
Usage: REACT_APP_BACKEND_URL=http://localhost:8000 pytest tests/ -v
"""
import os
import pytest
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the backend API, from env var or default to localhost."""
    url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8000").rstrip("/")
    return url


@pytest.fixture(scope="session")
def api(base_url):
    """Requests session with retry logic (handles Render cold-start)."""
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=2, status_forcelist=[502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.base_url = base_url
    return session


def api_get(session, path, **kwargs):
    """Helper: GET request with base_url prefix."""
    return session.get(f"{session.base_url}{path}", **kwargs)


def api_post(session, path, **kwargs):
    """Helper: POST request with base_url prefix."""
    return session.post(f"{session.base_url}{path}", **kwargs)
