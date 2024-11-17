from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    affiliation = Column(String)
    role = Column(String, default="user")  # 'user' or 'admin'
    
    jobs = relationship("Job", back_populates="owner")

class Job(Base):
    __tablename__ = "jobs"
    
    job_id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.user_id"))
    phase = Column(String, default="pending")
    approval_status = Column(String, default="awaiting_approval")
    parameters = Column(Text)
    creation_time = Column(DateTime, default=datetime.utcnow)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    results = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    owner = relationship("User", back_populates="jobs")
