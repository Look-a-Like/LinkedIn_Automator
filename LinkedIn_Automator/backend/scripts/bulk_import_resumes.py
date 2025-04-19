#!/usr/bin/env python
# Bulk Import Resume Script

import yaml
import requests
import json
import argparse
import os
import datetime
import sys
from tabulate import tabulate  # You'll need to install this: pip install tabulate


def load_yaml_resume(yaml_path):
    """Load resume data from a YAML file."""
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"YAML file not found: {yaml_path}")

    with open(yaml_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
        return data


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


def import_resume_to_api(yaml_data, api_url, token):
    """Import resume data to the API."""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    # Add metadata about the import
    yaml_data['import_source'] = 'bulk_import_resumes.py script'
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


def get_user_profile(api_url, token):
    """Get the user profile to verify connection."""
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(
        f"{api_url}/users/me/profile",
        headers=headers
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error getting user profile: {response.status_code} - {response.text}")


def bulk_import_resumes(directory, api_url, token):
    """Import all YAML resumes from a directory."""
    if not os.path.isdir(directory):
        raise ValueError(f"Directory not found: {directory}")

    results = []

    # Get list of YAML files
    yaml_files = [f for f in os.listdir(directory) if f.endswith(('.yaml', '.yml'))]

    if not yaml_files:
        print("No YAML files found in the directory.")
        return []

    # Process each file
    for i, file_name in enumerate(yaml_files):
        file_path = os.path.join(directory, file_name)
        print(f"Processing file {i + 1}/{len(yaml_files)}: {file_name}...")

        try:
            # Load YAML
            yaml_data = load_yaml_resume(file_path)

            # Import to API
            result = import_resume_to_api(yaml_data, api_url, token)

            # Add to results
            results.append({
                "file": file_name,
                "status": "SUCCESS",
                "resume_id": result.get("resume_id"),
                "name": yaml_data.get("personal_information", {}).get("name", "Unknown")
            })

            print(f"✅ Successfully imported: {file_name}")

        except Exception as e:
            print(f"❌ Error importing {file_name}: {str(e)}")
            results.append({
                "file": file_name,
                "status": "ERROR",
                "error": str(e),
                "name": "Unknown"
            })

    return results


def main():
    parser = argparse.ArgumentParser(description='Bulk import YAML resumes to the API')
    parser.add_argument('--directory', '-d', required=True, help='Directory containing YAML resume files')
    parser.add_argument('--api-url', default='http://localhost:8000', help='API URL')
    parser.add_argument('--email', required=True, help='User email for authentication')
    parser.add_argument('--password', required=True, help='User password for authentication')
    parser.add_argument('--output', '-o', help='Output file for import results (JSON)')

    args = parser.parse_args()

    try:
        print(f"Authenticating with API at {args.api_url}...")
        # Login and get token
        token = login_and_get_token(args.api_url, args.email, args.password)

        # Verify connection by getting user profile
        profile = get_user_profile(args.api_url, token)
        print(f"Authenticated as: {profile['user']['email']}")
        print(f"Current resume count: {profile['resume_stats']['count']}")

        # Bulk import resumes
        print(f"\nImporting resumes from directory: {args.directory}")
        results = bulk_import_resumes(args.directory, args.api_url, token)

        # Display summary table
        success_count = sum(1 for r in results if r["status"] == "SUCCESS")
        error_count = len(results) - success_count

        print("\n=== Import Summary ===")
        print(f"Total files: {len(results)}")
        print(f"Successfully imported: {success_count}")
        print(f"Failed: {error_count}")

        if results:
            # Create a table for display
            table_data = [
                [
                    r["file"],
                    r["status"],
                    r.get("resume_id", "N/A"),
                    r["name"]
                ] for r in results
            ]

            headers = ["File", "Status", "Resume ID", "Name"]
            print("\nDetailed Results:")
            print(tabulate(table_data, headers=headers, tablefmt="grid"))

        # Save results to file if specified
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": datetime.datetime.now().isoformat(),
                    "total": len(results),
                    "success_count": success_count,
                    "error_count": error_count,
                    "results": results
                }, f, indent=2)
            print(f"\nResults saved to: {args.output}")

        # Update user profile to show new resume count
        updated_profile = get_user_profile(args.api_url, token)
        print(f"\nUpdated resume count: {updated_profile['resume_stats']['count']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())