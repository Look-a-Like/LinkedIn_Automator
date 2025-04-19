from pydantic import BaseModel, EmailStr, Field
from typing import ClassVar, Dict, Any
from bson import ObjectId


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


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str = Field(...)  # Added user_id field

    model_config: ClassVar[Dict[str, Any]] = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            ObjectId: str
        },
        "json_schema_extra": {
            "example": {
                "_id": "60d5ec9af682dcbad2d1811a",
                "email": "user@example.com",
                "username": "johndoe",
                "user_id": "user_1234567890"
            }
        }
    }