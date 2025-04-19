# app/services/resume_import_service.py
import yaml
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId

from ..db import db
from ..utils.resume_utils import load_resume_from_yaml, validate_resume_data


class ResumeImportService:
    """Service for importing resume data from various formats"""

    @staticmethod
    async def import_from_yaml(yaml_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Import resume data from a YAML dictionary and save it to the database.

        Args:
            yaml_data: The parsed YAML data as a dictionary
            user_id: The user ID (string) who owns this resume

        Returns:
            Dictionary containing the imported resume data and its ID
        """
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        # Validate the resume data
        validation_errors = validate_resume_data(yaml_data)
        if validation_errors:
            raise ValueError(f"Resume validation failed: {', '.join(validation_errors)}")

        # Add metadata
        yaml_data["_import_info"] = {
            "source": "yaml_import",
            "import_date": datetime.utcnow().isoformat(),
            "version": "1.0"
        }

        # Create document to be inserted
        doc = {
            "user_id": ObjectId(user_id),
            "data": yaml_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "name": yaml_data.get("personal_information", {}).get("name", "Imported Resume"),
            "source": "yaml_import"
        }

        # Insert into MongoDB
        result = await db.resumes.insert_one(doc)

        # Get the inserted document
        created_resume = await db.resumes.find_one({"_id": result.inserted_id})

        return {
            "resume_id": str(result.inserted_id),
            "resume_data": created_resume
        }

    @staticmethod
    async def import_from_yaml_file(file_path: str, user_id: str) -> Dict[str, Any]:
        """
        Import resume data from a YAML file and save it to the database.

        Args:
            file_path: Path to the YAML file
            user_id: The user ID (string) who owns this resume

        Returns:
            Dictionary containing the imported resume data and its ID
        """
        # Load YAML data from file
        yaml_data = load_resume_from_yaml(file_path)

        # Import the data
        return await ResumeImportService.import_from_yaml(yaml_data, user_id)

    @staticmethod
    async def bulk_import_from_directory(directory_path: str, user_id: str) -> List[Dict[str, Any]]:
        """
        Import multiple resume YAML files from a directory.

        Args:
            directory_path: Path to the directory containing YAML files
            user_id: The user ID (string) who owns these resumes

        Returns:
            List of dictionaries containing the imported resume data and IDs
        """
        if not os.path.isdir(directory_path):
            raise ValueError(f"Directory not found: {directory_path}")

        results = []

        # Iterate through all YAML files in the directory
        for filename in os.listdir(directory_path):
            if filename.endswith(('.yaml', '.yml')):
                file_path = os.path.join(directory_path, filename)

                try:
                    # Import the file
                    import_result = await ResumeImportService.import_from_yaml_file(file_path, user_id)
                    results.append({
                        "filename": filename,
                        "success": True,
                        "resume_id": import_result["resume_id"]
                    })
                except Exception as e:
                    results.append({
                        "filename": filename,
                        "success": False,
                        "error": str(e)
                    })

        return results