# app/services/streamlit_auth.py
import requests
from typing import Dict, Any, Optional
import json


class StreamlitAuth:
    """Service for handling authentication between Streamlit and the FastAPI backend"""

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url

    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Login a user and return their token and info"""
        try:
            response = requests.post(
                f"{self.api_url}/users/login",
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Login error: {e}")
            return None

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a token is valid and return user info"""
        try:
            response = requests.get(
                f"{self.api_url}/users/me",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Token verification error: {e}")
            return None

    def get_user_resumes(self, token: str) -> Optional[Dict[str, Any]]:
        """Get all resumes for the authenticated user"""
        try:
            response = requests.get(
                f"{self.api_url}/resumes/",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Get user resumes error: {e}")
            return None