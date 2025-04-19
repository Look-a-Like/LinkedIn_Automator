# app/services/user_service.py
from bson import ObjectId
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..db import db
from ..utils.resume_utils import convert_objectid_to_str, convert_datetime_to_str


class UserService:
    """Service for user-related operations"""

    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by their ID"""
        if not ObjectId.is_valid(user_id):
            return None

        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            # Remove sensitive information
            if "hashed_password" in user:
                del user["hashed_password"]

            # Convert ObjectIds to strings
            user = convert_objectid_to_str(user)

            return user
        return None

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get a user by their email"""
        user = await db.users.find_one({"email": email})
        if user:
            # Remove sensitive information
            if "hashed_password" in user:
                del user["hashed_password"]

            # Convert ObjectIds to strings
            user = convert_objectid_to_str(user)

            return user
        return None

    @staticmethod
    async def get_user_resumes(user_id: str) -> List[Dict[str, Any]]:
        """Get all resumes for a specific user"""
        if not ObjectId.is_valid(user_id):
            return []

        user_obj_id = ObjectId(user_id)
        cursor = db.resumes.find({"user_id": user_obj_id})
        resumes = await cursor.to_list(length=100)

        # Process resumes for display
        processed_resumes = []
        for resume in resumes:
            # Convert ObjectIds and datetimes to strings
            resume = convert_objectid_to_str(resume)
            resume = convert_datetime_to_str(resume)
            processed_resumes.append(resume)

        return processed_resumes

    @staticmethod
    async def get_user_resume_by_id(user_id: str, resume_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific resume for a user by resume ID"""
        if not ObjectId.is_valid(user_id) or not ObjectId.is_valid(resume_id):
            return None

        user_obj_id = ObjectId(user_id)
        resume_obj_id = ObjectId(resume_id)

        resume = await db.resumes.find_one({
            "_id": resume_obj_id,
            "user_id": user_obj_id
        })

        if resume:
            # Convert ObjectIds and datetimes to strings
            resume = convert_objectid_to_str(resume)
            resume = convert_datetime_to_str(resume)
            return resume

        return None

    @staticmethod
    async def count_user_resumes(user_id: str) -> int:
        """Count the number of resumes a user has"""
        if not ObjectId.is_valid(user_id):
            return 0

        user_obj_id = ObjectId(user_id)
        count = await db.resumes.count_documents({"user_id": user_obj_id})
        return count

    @staticmethod
    async def get_latest_user_resume(user_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recently updated resume for a user"""
        if not ObjectId.is_valid(user_id):
            return None

        user_obj_id = ObjectId(user_id)
        # Find most recent resume sorted by updated_at
        resume = await db.resumes.find_one(
            {"user_id": user_obj_id},
            sort=[("updated_at", -1)]  # -1 for descending
        )

        if resume:
            # Convert ObjectIds and datetimes to strings
            resume = convert_objectid_to_str(resume)
            resume = convert_datetime_to_str(resume)
            return resume

        return None