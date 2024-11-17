from fastapi import FastAPI, Depends, HTTPException, status, Form, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import json

from database import Base, engine, SessionLocal
from models import User, Job
from schemas import UserCreate, User as UserSchema, JobCreate, Job as JobSchema
from auth import (
    authenticate_user, create_access_token, get_current_active_user, get_current_admin_user, get_db, get_password_hash, get_user
)

app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

@app.post("/token")
async def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=UserSchema)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        password_hash=hashed_password,
        affiliation=user.affiliation,
        role='user'
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/jobs", status_code=303)
async def create_job(
    job_create: JobCreate,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    job = Job(
        owner_id=current_user.user_id,
        phase='pending',
        approval_status='awaiting_approval',
        parameters=json.dumps(job_create.parameters),
        creation_time=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    response.headers["Location"] = f"/jobs/{job.job_id}"
    return {"job_id": job.job_id}

@app.get("/jobs/{job_id}", response_model=JobSchema)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.owner_id != current_user.user_id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")
    job.parameters = json.loads(job.parameters)
    return job

@app.get("/jobs", response_model=List[JobSchema])
async def list_jobs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role == 'admin':
        jobs = db.query(Job).all()
    else:
        jobs = db.query(Job).filter(Job.owner_id == current_user.user_id).all()
    for job in jobs:
        job.parameters = json.loads(job.parameters)
    return jobs

@app.post("/jobs/{job_id}/control")
async def control_job(
    job_id: int,
    action: str = Form(...),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if action == 'approve':
        job.approval_status = 'approved'
        job.phase = 'queued'
    elif action == 'reject':
        job.approval_status = 'rejected'
        job.phase = 'aborted'
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    db.commit()
    return {"status": "success"}

@app.post("/jobs/{job_id}/phase")
async def change_job_phase(
    job_id: int,
    phase: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if phase == 'aborted' and job.phase in ['pending', 'queued', 'executing']:
        job.phase = 'aborted'
        job.end_time = datetime.utcnow()
        db.commit()
        return {"status": "job aborted"}
    else:
        raise HTTPException(status_code=400, detail="Cannot change phase")

@app.get("/jobs/{job_id}/results")
async def get_job_results(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if job.phase != 'completed':
        raise HTTPException(status_code=400, detail="Job not completed")
    return {"results": json.loads(job.results)}
