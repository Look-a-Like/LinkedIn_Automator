# app/models/resume.py
from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Any, Optional, ClassVar, Union
from bson import ObjectId
from datetime import datetime


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, info=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema_generator, field_schema) -> Dict[str, Any]:
        field_schema.update(type="string")
        return field_schema


# Personal Information
class PersonalInformation(BaseModel):
    name: str
    surname: str
    date_of_birth: Optional[str] = ""
    country: Optional[str] = ""
    city: Optional[str] = ""
    address: Optional[str] = ""
    zip_code: Optional[str] = ""
    phone_prefix: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    github: Optional[str] = ""
    linkedin: Optional[str] = ""


# Education Details
class EducationDetail(BaseModel):
    education_level: Optional[str] = ""
    institution: Optional[str] = ""
    field_of_study: Optional[str] = ""
    final_evaluation_grade: Optional[str] = ""
    start_date: Optional[str] = ""
    year_of_completion: Optional[str] = ""


# Experience Details
class ExperienceDetail(BaseModel):
    position: Optional[str] = ""
    company: Optional[str] = ""
    employment_period: Optional[str] = ""
    location: Optional[str] = ""
    industry: Optional[str] = ""
    key_responsibilities: Optional[List[str]] = []
    skills_acquired: Optional[List[str]] = []


# Projects
class Project(BaseModel):
    name: str
    description: Optional[str] = ""
    link: Optional[str] = ""


# Achievements
class Achievement(BaseModel):
    name: str
    description: Optional[str] = ""


# Job Preferences
class JobPreferences(BaseModel):
    date_availability: Optional[str] = ""
    experience_level: Optional[List[str]] = []
    company_preferences: Optional[List[str]] = []
    workplace_type: Optional[List[str]] = []
    easy_apply_preferred: Optional[str] = ""


# Salary Expectations
class SalaryExpectations(BaseModel):
    salary_range_usd: Optional[str] = ""


# Self Identification
class SelfIdentification(BaseModel):
    gender: Optional[str] = ""
    pronouns: Optional[str] = ""
    veteran: Optional[str] = ""
    has_disability: Optional[str] = ""
    disability_description: Optional[str] = ""
    ethnicity: Optional[str] = ""


# Legal Authorization
class LegalAuthorization(BaseModel):
    work_authorization: Optional[str] = ""
    requires_visa: Optional[str] = ""
    legally_allowed_to_work_in_india: Optional[str] = ""
    requires_sponsorship: Optional[str] = ""


# Work Preferences
class WorkPreferences(BaseModel):
    remote_work: Optional[str] = ""
    in_person_work: Optional[str] = ""
    open_to_relocation: Optional[str] = ""
    willing_to_complete_assessments: Optional[str] = ""
    willing_to_undergo_drug_tests: Optional[str] = ""
    willing_to_undergo_background_checks: Optional[str] = ""


# Resume Model for creating/updating
class ResumeCreate(BaseModel):
    personal_information: PersonalInformation
    education_details: List[EducationDetail] = []
    experience_details: List[ExperienceDetail] = []
    projects: List[Project] = []
    achievements: List[Achievement] = []
    skills: List[str] = []
    certifications: List[str] = []
    languages: List[str] = []
    interests: List[str] = []
    availability: Dict[str, Any] = {}
    job_preferences: Optional[JobPreferences] = None
    salary_expectations: Optional[SalaryExpectations] = None
    self_identification: Optional[SelfIdentification] = None
    legal_authorization: Optional[LegalAuthorization] = None
    work_preferences: Optional[WorkPreferences] = None
    user_id: Optional[PyObjectId] = None  # Added user_id field

    class Config:
        populate_by_name = True


# Resume Model for responses
class ResumeResponse(ResumeCreate):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config: ClassVar[Dict[str, Any]] = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
    }


# Simple Schema-less Model
class ResumeData(BaseModel):
    user_id: PyObjectId
    data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config: ClassVar[Dict[str, Any]] = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
    }


# Resume Model with ID for database responses
class ResumeInDB(ResumeData):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")