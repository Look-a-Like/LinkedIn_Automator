# streamlit_auth_helper.py
import streamlit as st
import requests
import json
from typing import Dict, Any, Optional


class AuthHelper:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url

    def login(self, email: str, password: str) -> bool:
        """Login a user and store their token in session state"""
        try:
            response = requests.post(
                f"{self.api_url}/users/login",
                json={"email": email, "password": password},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()
                # Store in Streamlit session state
                st.session_state["auth_token"] = data["access_token"]
                st.session_state["user"] = data["user"]
                st.session_state["authenticated"] = True
                return True
            else:
                st.error(f"Login failed: {response.json().get('detail', 'Unknown error')}")
                return False
        except Exception as e:
            st.error(f"Connection error: {str(e)}")
            return False

    def logout(self):
        """Clear authentication from session state"""
        if "auth_token" in st.session_state:
            del st.session_state["auth_token"]
        if "user" in st.session_state:
            del st.session_state["user"]
        st.session_state["authenticated"] = False

    def is_authenticated(self) -> bool:
        """Check if the user is authenticated"""
        if "auth_token" not in st.session_state:
            return False

        # Verify token is still valid
        try:
            response = requests.get(
                f"{self.api_url}/users/verify-token",
                headers={
                    "Authorization": f"Bearer {st.session_state['auth_token']}",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code == 200:
                return True
            else:
                # Clear invalid token
                self.logout()
                return False
        except Exception:
            # If verification fails, consider not authenticated
            self.logout()
            return False

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get the current authenticated user"""
        if not self.is_authenticated():
            return None
        return st.session_state.get("user")

    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        headers = {"Content-Type": "application/json"}
        if "auth_token" in st.session_state:
            headers["Authorization"] = f"Bearer {st.session_state['auth_token']}"
        return headers

    # Add methods for specific API calls
    def get_user_resumes(self) -> Optional[Dict[str, Any]]:
        """Get all resumes for the current user"""
        if not self.is_authenticated():
            return None

        try:
            response = requests.get(
                f"{self.api_url}/resumes/",
                headers=self.get_auth_headers()
            )

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            st.error(f"Error fetching resumes: {str(e)}")
            return None

    def import_resume(self, resume_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Import a resume from YAML data"""
        if not self.is_authenticated():
            return None

        try:
            response = requests.post(
                f"{self.api_url}/resumes/import",
                json=resume_data,
                headers=self.get_auth_headers()
            )

            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Error importing resume: {response.json().get('detail', 'Unknown error')}")
            return None
        except Exception as e:
            st.error(f"Error importing resume: {str(e)}")
            return None