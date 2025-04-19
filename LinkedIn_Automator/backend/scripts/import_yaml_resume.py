#!/usr/bin/env python
# Import YAML Resume Example Script

import yaml
import requests
import json
import argparse
import os
import datetime


def load_yaml_resume(yaml_path):
    """Load resume data from a YAML file."""
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"YAML file not found: {yaml_path}")

    with open(yaml_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
        return data


def import_resume_to_api(yaml_data, api_url, token):
    """Import resume data to the API."""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    # Perform data cleanup and validation before sending
    # Add some metadata about the import
    yaml_data['import_source'] = 'import_yaml_resume.py script'
    yaml_data['import_timestamp'] = datetime.datetime.now().isoformat()

    response = requests.post(
        f"{api_url}/resumes/import",
        headers=headers,
        json=yaml_data
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API Error: {response.status_code} - {response.text}")


def login_and_get_token(api_url, email, password):
    """Login to the API and get authentication token."""
    headers = {
        'Content-Type': 'application/json'
    }

    login_data = {
        'email': email,
        'password': password
    }

    response = requests.post(
        f"{api_url}/users/login",
        headers=headers,
        json=login_data
    )

    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Login Error: {response.status_code} - {response.text}")


def main():
    parser = argparse.ArgumentParser(description='Import YAML resume to the API')
    parser.add_argument('yaml_path', help='Path to the YAML resume file')
    parser.add_argument('--api-url', default='http://localhost:8000', help='API URL')
    parser.add_argument('--email', required=True, help='User email for authentication')
    parser.add_argument('--password', required=True, help='User password for authentication')

    args = parser.parse_args()

    try:
        # Load YAML data
        yaml_data = load_yaml_resume(args.yaml_path)

        # Login and get token
        token = login_and_get_token(args.api_url, args.email, args.password)

        # Import resume
        result = import_resume_to_api(yaml_data, args.api_url, token)

        print(json.dumps(result, indent=2))
        print(f"\nResume imported successfully with ID: {result['resume_id']}")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())