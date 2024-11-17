from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str
    affiliation: Optional[str] = None

class User(BaseModel):
    user_id: int
    username: str
    affiliation: Optional[str] = None
    role: str

    class Config:
        orm_mode = True

class JobCreate(BaseModel):
    parameters: dict  # Parameters for the job

class Job(BaseModel):
    job_id: int
    owner_id: int
    phase: str
    approval_status: str
    parameters: dict
    creation_time: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    results: Optional[Any] = None
    error_message: Optional[str] = None

    class Config:
        orm_mode = True
