# app/routes/Resume.py
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict, Any
from datetime import datetime
from bson import ObjectId

from ..models.resume import ResumeCreate, ResumeResponse, ResumeData, ResumeInDB
from ..db import db

# Ensure this is correctly imported and defined in User.py
from ..routes.User import get_current_user

router = APIRouter(
    prefix="/resumes",
    tags=["resumes"],
    responses={404: {"description": "Not found"}},
)


def convert_objectid_to_str(obj):
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


@router.get("/latest", response_model=Dict[str, Any])
async def get_latest_resume(current_user: dict = Depends(get_current_user)):
    user_id = current_user["_id"]
    resume = await db.resumes.find_one(
        {"user_id": user_id},
        sort=[("created_at", -1)]
    )
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found")
    resume = convert_objectid_to_str(resume)
    return {
        "message": "Latest resume retrieved successfully",
        "resume": resume
    }


@router.post("/", response_model=Dict[str, Any])
async def create_resume(
    resume_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["_id"]
    doc = {
        "user_id": user_id,
        "data": resume_data,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await db.resumes.insert_one(doc)
    created_resume = await db.resumes.find_one({"_id": result.inserted_id})
    created_resume = convert_objectid_to_str(created_resume)
    return {
        "message": "Resume created successfully",
        "resume_id": str(result.inserted_id),
        "resume": created_resume
    }


@router.get("/", response_model=Dict[str, Any])
async def get_all_resumes(current_user: dict = Depends(get_current_user)):
    user_id = current_user["_id"]
    cursor = db.resumes.find({"user_id": user_id})
    resumes = await cursor.to_list(length=100)
    resumes = convert_objectid_to_str(resumes)
    return {
        "count": len(resumes),
        "resumes": resumes
    }


@router.get("/{resume_id}", response_model=Dict[str, Any])
async def get_resume(resume_id: str, current_user: dict = Depends(get_current_user)):
    try:
        resume_obj_id = ObjectId(resume_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid resume ID format")
    user_id = current_user["_id"]
    resume = await db.resumes.find_one({
        "_id": resume_obj_id,
        "user_id": user_id
    })
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    resume = convert_objectid_to_str(resume)
    return {"resume": resume}


@router.put("/{resume_id}", response_model=Dict[str, Any])
async def update_resume(
    resume_id: str,
    resume_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        resume_obj_id = ObjectId(resume_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid resume ID format")
    user_id = current_user["_id"]
    existing_resume = await db.resumes.find_one({
        "_id": resume_obj_id,
        "user_id": user_id
    })
    if not existing_resume:
        raise HTTPException(status_code=404, detail="Resume not found or access denied")
    update_data = {
        "data": resume_data,
        "updated_at": datetime.utcnow()
    }
    await db.resumes.update_one({"_id": resume_obj_id}, {"$set": update_data})
    updated_resume = await db.resumes.find_one({"_id": resume_obj_id})
    updated_resume = convert_objectid_to_str(updated_resume)
    return {
        "message": "Resume updated successfully",
        "resume": updated_resume
    }


@router.delete("/{resume_id}", response_model=Dict[str, Any])
async def delete_resume(
    resume_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        resume_obj_id = ObjectId(resume_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid resume ID format")
    user_id = current_user["_id"]
    existing_resume = await db.resumes.find_one({
        "_id": resume_obj_id,
        "user_id": user_id
    })
    if not existing_resume:
        raise HTTPException(status_code=404, detail="Resume not found or access denied")
    result = await db.resumes.delete_one({"_id": resume_obj_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete resume")
    return {
        "message": "Resume deleted successfully",
        "resume_id": resume_id
    }


@router.post("/import", response_model=Dict[str, Any])
async def import_yaml_resume(
    yaml_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["_id"]
    doc = {
        "user_id": user_id,
        "data": yaml_data,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await db.resumes.insert_one(doc)
    created_resume = await db.resumes.find_one({"_id": result.inserted_id})
    created_resume = convert_objectid_to_str(created_resume)
    return {
        "message": "Resume imported successfully",
        "resume_id": str(result.inserted_id),
        "resume": created_resume
    }
