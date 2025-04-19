# app/utils/resume_utils.py
import yaml
import json
import os
from bson import ObjectId
from typing import Dict, Any, List, Optional
from datetime import datetime


def load_resume_from_yaml(yaml_path: str) -> Dict[str, Any]:
    """Load resume data from a YAML file."""
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"YAML file not found: {yaml_path}")

    with open(yaml_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
        return data


def save_resume_as_yaml(resume_data: Dict[str, Any], yaml_path: str) -> None:
    """Save resume data to a YAML file."""
    with open(yaml_path, 'w', encoding='utf-8') as file:
        yaml.dump(resume_data, file, default_flow_style=False)


def convert_objectid_to_str(obj: Any) -> Any:
    """Convert ObjectId to string in nested dictionaries and lists."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, ObjectId):
                obj[key] = str(value)
            elif isinstance(value, (dict, list)):
                convert_objectid_to_str(value)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, ObjectId):
                obj[i] = str(item)
            elif isinstance(item, (dict, list)):
                convert_objectid_to_str(item)
    return obj


def convert_datetime_to_str(obj: Any) -> Any:
    """Convert datetime to ISO string in nested dictionaries and lists."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, datetime):
                obj[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                convert_datetime_to_str(value)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, datetime):
                obj[i] = item.isoformat()
            elif isinstance(item, (dict, list)):
                convert_datetime_to_str(item)
    return obj


def prepare_resume_for_export(resume_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare resume data for export by converting ObjectId and datetime objects
    to strings and extracting actual resume data from the database structure.
    """
    # Deep copy the data to avoid modifying the original
    import copy
    data = copy.deepcopy(resume_data)

    # Convert ObjectId and datetime to strings
    data = convert_objectid_to_str(data)
    data = convert_datetime_to_str(data)

    # If the data has a "data" field, extract it (for schema-less storage)
    if "data" in data:
        return data["data"]

    # Otherwise, clean up the document by removing MongoDB-specific fields
    if "_id" in data:
        del data["_id"]
    if "user_id" in data:
        del data["user_id"]
    if "created_at" in data:
        del data["created_at"]
    if "updated_at" in data:
        del data["updated_at"]

    return data


def validate_resume_data(resume_data: Dict[str, Any]) -> List[str]:
    """
    Validate resume data structure and return a list of validation errors.
    Returns an empty list if the data is valid.
    """
    errors = []

    # Check for required fields
    required_sections = [
        "personal_information",
        "education_details",
        "skills"
    ]

    for section in required_sections:
        if section not in resume_data:
            errors.append(f"Missing required section: {section}")

    # Validate personal information
    if "personal_information" in resume_data:
        personal_info = resume_data["personal_information"]

        # Check required personal fields
        for field in ["name", "email"]:
            if field not in personal_info or not personal_info[field]:
                errors.append(f"Missing required field: personal_information.{field}")

    # Validate education_details if present
    if "education_details" in resume_data and isinstance(resume_data["education_details"], list):
        for i, edu in enumerate(resume_data["education_details"]):
            if not isinstance(edu, dict):
                errors.append(f"Education detail at index {i} is not a dictionary")
                continue

            # Check for key education fields
            for field in ["institution", "field_of_study"]:
                if field not in edu or not edu.get(field):
                    errors.append(f"Missing recommended field: education_details[{i}].{field}")

    return errors


def find_duplicates_in_resume(resume_data: Dict[str, Any]) -> Dict[str, List]:
    """Find duplicate entries in various resume sections."""
    duplicates = {}

    # Check for duplicate skills
    if "skills" in resume_data and isinstance(resume_data["skills"], list):
        skill_counts = {}
        for skill in resume_data["skills"]:
            if skill in skill_counts:
                skill_counts[skill] += 1
            else:
                skill_counts[skill] = 1

        # Add duplicates to the result
        skill_dups = [skill for skill, count in skill_counts.items() if count > 1]
        if skill_dups:
            duplicates["skills"] = skill_dups

    # Check for duplicate education entries
    if "education_details" in resume_data and isinstance(resume_data["education_details"], list):
        edu_entries = {}
        for edu in resume_data["education_details"]:
            if isinstance(edu, dict):
                key = (edu.get("institution", ""), edu.get("field_of_study", ""))
                if key in edu_entries:
                    edu_entries[key] += 1
                else:
                    edu_entries[key] = 1

        # Add duplicates to the result
        edu_dups = [f"{inst} - {field}" for (inst, field), count in edu_entries.items() if count > 1]
        if edu_dups:
            duplicates["education_details"] = edu_dups

    return duplicates


def extract_skills_from_resume(resume_data: Dict[str, Any]) -> List[str]:
    """Extract and normalize skills from resume data."""
    skills = []

    # Get explicitly listed skills
    if "skills" in resume_data and isinstance(resume_data["skills"], list):
        skills.extend(resume_data["skills"])

    # Extract skills from experience descriptions
    if "experience_details" in resume_data and isinstance(resume_data["experience_details"], list):
        for exp in resume_data["experience_details"]:
            if isinstance(exp, dict) and "skills_acquired" in exp and isinstance(exp["skills_acquired"], list):
                skills.extend(exp["skills_acquired"])

    # Extract skills from project descriptions
    if "projects" in resume_data and isinstance(resume_data["projects"], list):
        for proj in resume_data["projects"]:
            if isinstance(proj, dict) and "description" in proj:
                # This is a simple approach; in a real implementation, you might use
                # NLP techniques to extract skills from descriptions
                desc = proj["description"].lower()
                # Example of common technical skills to look for
                common_skills = ["python", "javascript", "react", "node", "mongodb", "sql",
                                 "java", "c++", "fastapi", "docker", "aws", "azure",
                                 "machine learning", "tensorflow", "pytorch"]
                for skill in common_skills:
                    if skill in desc and skill not in skills:
                        skills.append(skill)

    # Normalize skills (make case consistent, remove duplicates)
    normalized_skills = []
    seen = set()
    for skill in skills:
        skill_lower = skill.lower()
        if skill_lower not in seen:
            seen.add(skill_lower)
            # Use the original case for the normalized list
            normalized_skills.append(skill)

    return normalized_skills


def compare_resumes(resume1: Dict[str, Any], resume2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two resumes and return differences.

    Args:
        resume1: First resume data dictionary
        resume2: Second resume data dictionary

    Returns:
        Dictionary with sections comparing the two resumes
    """
    comparison = {}

    # Compare skills
    skills1 = set(extract_skills_from_resume(resume1))
    skills2 = set(extract_skills_from_resume(resume2))

    unique_skills1 = skills1 - skills2
    unique_skills2 = skills2 - skills1
    common_skills = skills1.intersection(skills2)

    comparison["skills"] = {
        "only_in_resume1": list(unique_skills1),
        "only_in_resume2": list(unique_skills2),
        "common": list(common_skills)
    }

    # Compare education
    edu1 = {(e.get("institution", ""), e.get("field_of_study", ""))
            for e in resume1.get("education_details", []) if isinstance(e, dict)}
    edu2 = {(e.get("institution", ""), e.get("field_of_study", ""))
            for e in resume2.get("education_details", []) if isinstance(e, dict)}

    unique_edu1 = edu1 - edu2
    unique_edu2 = edu2 - edu1
    common_edu = edu1.intersection(edu2)

    comparison["education"] = {
        "only_in_resume1": [{"institution": inst, "field_of_study": field} for inst, field in unique_edu1],
        "only_in_resume2": [{"institution": inst, "field_of_study": field} for inst, field in unique_edu2],
        "common": [{"institution": inst, "field_of_study": field} for inst, field in common_edu]
    }

    # Compare experience count
    exp_count1 = len(resume1.get("experience_details", []))
    exp_count2 = len(resume2.get("experience_details", []))

    comparison["experience_count"] = {
        "resume1": exp_count1,
        "resume2": exp_count2,
        "difference": exp_count1 - exp_count2
    }

    # Compare projects count
    proj_count1 = len(resume1.get("projects", []))
    proj_count2 = len(resume2.get("projects", []))

    comparison["projects_count"] = {
        "resume1": proj_count1,
        "resume2": proj_count2,
        "difference": proj_count1 - proj_count2
    }

    return comparison


def merge_resumes(main_resume: Dict[str, Any], secondary_resume: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two resumes, with the main_resume taking precedence for conflicting fields.

    Args:
        main_resume: Primary resume data dictionary
        secondary_resume: Secondary resume data dictionary to merge from

    Returns:
        Merged resume data dictionary
    """
    # Deep copy the main resume to avoid modifying the original
    import copy
    merged = copy.deepcopy(main_resume)

    # Merge skills (add unique skills from secondary resume)
    if "skills" in secondary_resume and isinstance(secondary_resume["skills"], list):
        if "skills" not in merged:
            merged["skills"] = []

        # Add skills from secondary resume if they don't exist in main resume
        for skill in secondary_resume["skills"]:
            if skill not in merged["skills"]:
                merged["skills"].append(skill)

    # Merge education_details
    if "education_details" in secondary_resume and isinstance(secondary_resume["education_details"], list):
        if "education_details" not in merged:
            merged["education_details"] = []

        # Create a set of tuples with institution and field for existing education
        existing_edu = {(edu.get("institution", ""), edu.get("field_of_study", ""))
                        for edu in merged["education_details"] if isinstance(edu, dict)}

        # Add education from secondary resume if not in main resume
        for edu in secondary_resume["education_details"]:
            if isinstance(edu, dict):
                key = (edu.get("institution", ""), edu.get("field_of_study", ""))
                if key not in existing_edu:
                    merged["education_details"].append(copy.deepcopy(edu))

    # Similar logic for experience_details, projects, achievements, etc.
    for section in ["experience_details", "projects", "achievements"]:
        if section in secondary_resume and isinstance(secondary_resume[section], list):
            if section not in merged:
                merged[section] = []

            # For simplicity, we'll use a name-based comparison
            existing_items = {item.get("name", "") for item in merged[section] if isinstance(item, dict)}

            # Add items from secondary resume if not in main resume
            for item in secondary_resume[section]:
                if isinstance(item, dict) and item.get("name", "") not in existing_items:
                    merged[section].append(copy.deepcopy(item))

    return merged