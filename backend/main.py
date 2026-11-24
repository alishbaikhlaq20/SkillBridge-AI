from fastapi import FastAPI, HTTPException, Depends,UploadFile, File
import json
from fastapi.middleware.cors import CORSMiddleware
from services.skill_gap import generate_skill_gaps
from services.matching import calculate_match
from sqlalchemy.orm import Session
from services.job_ai import analyze_job_with_ai
from services.gemini_client import GeminiServiceError
from routers import learning_plans
from database import get_db
from security import hash_password, verify_password
from models import User
from auth import create_access_token, get_current_user
from schemas import (
    UserCreate,
    UserLogin,
    ProfileCreate,
    JobAnalysisCreate,
    LearningPlanRequest,
    TaskUpdate,
    ResumeSkillAdditionUpdate,
)
from services.resume_ai import extract_resume_with_ai
from resume_parser import parse_resume
from models import (
    User,
    Profile,
    Resume,
    ResumeSkill,
    ResumeEducation,
    ResumeExperience,
    JobAnalysis,
    MatchResult,
    ResumeSkillAddition,
)
from database import Base, engine
import os
import logging
from pypdf import PdfReader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Career Intelligence API",
    description="Backend API for the AI Career Intelligence Platform",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(learning_plans.router)

@app.get("/")
def root():
    return {
        "message": "AI Career Intelligence API is running!"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }



@app.post("/register")
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = hash_password(user.password)

    new_user = User(
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully!",
        "user_id": new_user.id,
        "email": new_user.email,
        "full_name": new_user.full_name
    }
@app.post("/login")
def login_user(
    user: UserLogin,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        user.password,
        existing_user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(existing_user.id)

    return {
        "message": "Login successful!",
        "access_token": access_token,
        "user_id": existing_user.id,
        "email": existing_user.email,
        "full_name": existing_user.full_name
    }
@app.get("/profile")
def get_profile(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name
    }
@app.post("/profile")
def create_profile(
    profile: ProfileCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing_profile = db.query(Profile).filter(
        Profile.user_id == user_id
    ).first()

    if existing_profile:
        raise HTTPException(
            status_code=400,
            detail="Profile already exists"
        )

    new_profile = Profile(
        user_id=user_id,
        **profile.model_dump()
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return {
        "message": "Profile created successfully!",
        "profile_id": new_profile.id
    }
@app.get("/profile/details")
def get_profile_details(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(Profile).filter(
        Profile.user_id == user_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )

    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "phone": profile.phone,
        "location": profile.location,
        "education": profile.education,
        "university": profile.university,
        "degree": profile.degree,
        "graduation_year": profile.graduation_year,
        "experience_years": profile.experience_years,
        "bio": profile.bio,
        "linkedin_url": profile.linkedin_url,
        "github_url": profile.github_url,
        "portfolio_url": profile.portfolio_url,
    }
@app.put("/profile")
def update_profile(
    profile_data: ProfileCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(Profile).filter(
        Profile.user_id == user_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )

    for field, value in profile_data.model_dump().items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return {
        "message": "Profile updated successfully!",
        "profile_id": profile.id
    }
@app.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only allow PDF files
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # Read the file
    file_content = await file.read()

    # Limit file size to 5 MB
    max_size = 5 * 1024 * 1024

    if len(file_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail="File size must be less than 5 MB"
        )

    # Create uploads directory if it doesn't exist
    upload_directory = "uploads"
    os.makedirs(upload_directory, exist_ok=True)

    # Create a unique filename
    file_name = file.filename or "resume.pdf"
    safe_file_name = f"{user_id}_{file_name}"

    file_path = os.path.join(
        upload_directory,
        safe_file_name
    )

    # Save the PDF
    with open(file_path, "wb") as buffer:
        buffer.write(file_content)

    # Extract text from PDF
    try:
        reader = PdfReader(file_path)

        extracted_text = ""

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                extracted_text += page_text + "\n"

    except Exception:
        # Delete file if PDF processing fails
        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=400,
            detail="Could not read the PDF file"
        )

    # Save resume information in database
    new_resume = Resume(
        user_id=user_id,
        file_name=file_name,
        file_path=file_path,
        file_type=file.content_type,
        file_size=len(file_content),
        extracted_text=extracted_text
    )

    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)

    return {
        "message": "Resume uploaded successfully!",
        "resume_id": new_resume.id,
        "file_name": new_resume.file_name,
        "extracted_text_length": len(extracted_text)
    }
@app.get("/resume")
def get_resume(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = db.query(Resume).filter(
        Resume.user_id == user_id
    ).order_by(
        Resume.uploaded_at.desc()
    ).first()

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="No resume found"
        )

    return {
        "id": resume.id,
        "file_name": resume.file_name,
        "file_type": resume.file_type,
        "file_size": resume.file_size,
        "extracted_text_length": len(
            resume.extracted_text or ""
        ),
        "uploaded_at": resume.uploaded_at
    }
@app.post("/resume/analyze")
def analyze_resume(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = db.query(Resume).filter(
        Resume.user_id == user_id
    ).order_by(
        Resume.uploaded_at.desc()
    ).first()

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="No resume found"
        )

    # Parse the extracted resume text
    parsed_data = parse_resume(
        resume.extracted_text or ""
    )

    # Remove previously extracted data
    db.query(ResumeSkill).filter(
        ResumeSkill.resume_id == resume.id
    ).delete()

    db.query(ResumeEducation).filter(
        ResumeEducation.resume_id == resume.id
    ).delete()

    db.query(ResumeExperience).filter(
        ResumeExperience.resume_id == resume.id
    ).delete()

    # Save skills
    for skill in parsed_data["skills"]:
        new_skill = ResumeSkill(
            resume_id=resume.id,
            skill_name=skill
        )

        db.add(new_skill)

    # Save education
    education_text = parsed_data["education"].strip()

    if education_text:
        education = ResumeEducation(
            resume_id=resume.id,
            degree=education_text
        )

        db.add(education)

    # Save experience
    experience_text = parsed_data["experience"].strip()

    if experience_text:
        experience = ResumeExperience(
            resume_id=resume.id,
            description=experience_text
        )

        db.add(experience)

    db.commit()

    return {
        "message": "Resume analyzed successfully!",
        "resume_id": resume.id,
        "skills_found": len(parsed_data["skills"]),
        "skills": parsed_data["skills"],
        "education_detected": bool(education_text),
        "experience_detected": bool(experience_text)
    }
@app.post("/resume/ai-analyze")
def ai_analyze_resume(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get the user's latest resume
    resume = db.query(Resume).filter(
        Resume.user_id == user_id
    ).order_by(
        Resume.uploaded_at.desc()
    ).first()

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="No resume found"
        )

    # Make sure extracted text exists
    resume_text = resume.extracted_text or ""

    if not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Resume does not contain extractable text"
        )

    # Send resume text to Gemini
    try:
        ai_result = extract_resume_with_ai(resume_text)

    except GeminiServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"AI resume analysis failed: {e.message}"
        )

    except Exception:
        logger.exception("Unexpected error during AI resume analysis")
        raise HTTPException(
            status_code=500,
            detail="AI resume analysis failed due to an unexpected server error."
        )

    # Remove previous AI analysis for this resume
    db.query(ResumeSkill).filter(
        ResumeSkill.resume_id == resume.id
    ).delete()

    db.query(ResumeEducation).filter(
        ResumeEducation.resume_id == resume.id
    ).delete()

    db.query(ResumeExperience).filter(
        ResumeExperience.resume_id == resume.id
    ).delete()

    # -----------------------------
    # Save AI-extracted skills
    # -----------------------------

    for skill in ai_result.skills:

        new_skill = ResumeSkill(
            resume_id=resume.id,
            skill_name=skill
        )

        db.add(new_skill)

    # -----------------------------
    # Save AI-extracted education
    # -----------------------------

    for education in ai_result.education:

        new_education = ResumeEducation(
            resume_id=resume.id,
            degree=education.degree,
            university=education.university,
            location=education.location,
            cgpa=str(education.cgpa) if education.cgpa is not None else None,
            graduation_year=education.graduation_year
        )

        db.add(new_education)

    # -----------------------------
    # Save AI-extracted experience
    # -----------------------------

    for experience in ai_result.experience:

        new_experience = ResumeExperience(
            resume_id=resume.id,
            job_title=experience.job_title,
            company=experience.company,
            start_date=experience.start_date,
            end_date=experience.end_date,
            description="\n".join(
                experience.description
            )
        )

        db.add(new_experience)

    # Save everything
    db.commit()

    return {
        "message": "AI resume analysis completed successfully!",
        "resume_id": resume.id,

        "skills": ai_result.skills,

        "education": [
            education.model_dump()
            for education in ai_result.education
        ],

        "experience": [
            experience.model_dump()
            for experience in ai_result.experience
        ]
    }
@app.get("/resume/analysis")
def get_resume_analysis(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resume = db.query(Resume).filter(
        Resume.user_id == user_id
    ).order_by(
        Resume.uploaded_at.desc()
    ).first()

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="No resume found"
        )

    skills = db.query(ResumeSkill).filter(
        ResumeSkill.resume_id == resume.id
    ).all()

    education = db.query(ResumeEducation).filter(
        ResumeEducation.resume_id == resume.id
    ).all()

    experience = db.query(ResumeExperience).filter(
        ResumeExperience.resume_id == resume.id
    ).all()

    return {
        "resume_id": resume.id,
        "file_name": resume.file_name,

        "skills": [
            skill.skill_name
            for skill in skills
        ],

        "education": [
    {
        "degree": item.degree,
        "university": item.university,
        "location": item.location,
        "cgpa": item.cgpa,
        "graduation_year": item.graduation_year
    }
    for item in education
],

        "experience": [
            {
                "job_title": item.job_title,
                "company": item.company,
                "start_date": item.start_date,
                "end_date": item.end_date,
                "description": item.description
            }
            for item in experience
        ]
    }
@app.post("/jobs")
def create_job_analysis(
    job: JobAnalysisCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_job = JobAnalysis(
        user_id=user_id,
        description=job.description
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return {
        "message": "Job description saved successfully.",
        "job_id": new_job.id,
        "description": new_job.description
    }
@app.post("/jobs/{job_id}/analyze")
def analyze_job(
    job_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(JobAnalysis).filter(
        JobAnalysis.id == job_id,
        JobAnalysis.user_id == user_id
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job description not found"
        )

    if not job.description.strip():
        raise HTTPException(
            status_code=400,
            detail="Job description is empty"
        )

    try:
        ai_result = analyze_job_with_ai(
            job.description
        )

    except GeminiServiceError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"AI job analysis failed: {e.message}"
        )

    except Exception:
        logger.exception(
            "Unexpected error during AI job analysis (job_id=%s)", job_id
        )
        raise HTTPException(
            status_code=500,
            detail="AI job analysis failed due to an unexpected server error."
        )

    job.job_title = ai_result.job_title
    job.company = ai_result.company

    job.required_skills = json.dumps(
        ai_result.required_skills
    )

    job.preferred_skills = json.dumps(
        ai_result.preferred_skills
    )

    job.education_requirements = json.dumps(
        ai_result.education_requirements
    )

    job.experience_requirements = json.dumps(
        ai_result.experience_requirements
    )

    job.responsibilities = json.dumps(
        ai_result.responsibilities
    )

    db.commit()
    db.refresh(job)

    return {
        "message": "AI job analysis completed successfully.",
        "job_id": job.id,
        "job_title": job.job_title,
        "company": job.company,
        "required_skills": ai_result.required_skills,
        "preferred_skills": ai_result.preferred_skills,
        "education_requirements": ai_result.education_requirements,
        "experience_requirements": ai_result.experience_requirements,
        "responsibilities": ai_result.responsibilities
    }
@app.post("/match/{job_id}")
def create_match(
    job_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = (
        db.query(Resume)
        .filter(Resume.user_id == current_user)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="No resume found. Please upload and analyze your resume first.",
        )

    job = (
        db.query(JobAnalysis)
        .filter(
            JobAnalysis.id == job_id,
            JobAnalysis.user_id == current_user,
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job analysis not found.",
        )

    resume_skills = (
        db.query(ResumeSkill)
        .filter(ResumeSkill.resume_id == resume.id)
        .all()
    )

    resume_education = (
        db.query(ResumeEducation)
        .filter(ResumeEducation.resume_id == resume.id)
        .all()
    )

    resume_experience = (
        db.query(ResumeExperience)
        .filter(ResumeExperience.resume_id == resume.id)
        .all()
    )

    required_skills = (
        json.loads(job.required_skills)
        if job.required_skills
        else []
    )

    preferred_skills = (
        json.loads(job.preferred_skills)
        if job.preferred_skills
        else []
    )

    education_requirements = (
        json.loads(job.education_requirements)
        if job.education_requirements
        else []
    )

    experience_requirements = (
        json.loads(job.experience_requirements)
        if job.experience_requirements
        else []
    )

    result = calculate_match(
        resume_skills=[
            skill.skill_name
            for skill in resume_skills
        ],

        resume_experience=[
            {
                "job_title": experience.job_title,
                "company": experience.company,
                "start_date": experience.start_date,
                "end_date": experience.end_date,
                "description": experience.description,
            }
            for experience in resume_experience
        ],

        resume_education=[
            {
                "degree": education.degree,
                "university": education.university,
            }
            for education in resume_education
        ],

        required_skills=required_skills,
        preferred_skills=preferred_skills,
        experience_requirements=experience_requirements,
        education_requirements=education_requirements,
    )

    # Reuse the existing result for this user + resume + job instead of
    # inserting a new row every time the page is opened. The scores are
    # recalculated and overwritten, so they always reflect the latest data.
    match_result = (
        db.query(MatchResult)
        .filter(
            MatchResult.user_id == current_user,
            MatchResult.resume_id == resume.id,
            MatchResult.job_id == job.id,
        )
        .order_by(MatchResult.id.desc())
        .first()
    )

    if match_result is None:
        match_result = MatchResult(
            user_id=current_user,
            resume_id=resume.id,
            job_id=job.id,
        )
        db.add(match_result)

    match_result.overall_score = result.overall_score
    match_result.skills_score = result.skills_score
    match_result.experience_score = result.experience_score
    match_result.education_score = result.education_score
    match_result.matching_skills = json.dumps(result.matching_skills)
    match_result.missing_skills = json.dumps(result.missing_skills)

    db.commit()
    db.refresh(match_result)

    return {
        "message": "Resume and job matched successfully.",
        "match_id": match_result.id,
        "job_id": job.id,
        "overall_score": result.overall_score,
        "skills_score": result.skills_score,
        "experience_score": result.experience_score,
        "education_score": result.education_score,
        "matching_skills": result.matching_skills,
        "missing_skills": result.missing_skills,
    }
@app.post("/skill-gaps/{match_id}")
def get_skill_gaps(
    match_id: int,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    match_result = (
        db.query(MatchResult)
        .filter(
            MatchResult.id == match_id,
            MatchResult.user_id == current_user,
        )
        .first()
    )

    if not match_result:
        raise HTTPException(
            status_code=404,
            detail="Match result not found.",
        )

    missing_skills = (
        json.loads(match_result.missing_skills)
        if match_result.missing_skills
        else []
    )

    # The job tells us which missing skills were required and which were
    # only preferred, which drives the priority of each gap.
    job = (
        db.query(JobAnalysis)
        .filter(
            JobAnalysis.id == match_result.job_id,
            JobAnalysis.user_id == current_user,
        )
        .first()
    )

    required_skills = (
        json.loads(job.required_skills)
        if job and job.required_skills
        else []
    )

    gaps = generate_skill_gaps(missing_skills, required_skills)

    return {
        "match_id": match_result.id,
        "job_id": match_result.job_id,
        "overall_score": match_result.overall_score,
        "skill_gap_count": len(gaps),
        "skill_gaps": [
            {
                "skill": gap.skill,
                "category": gap.category,
                "priority": gap.priority,
                "reason": gap.reason,
            }
            for gap in gaps
        ],
    }
@app.get("/resume/skill-additions")
def get_approved_resume_skill_additions(
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Find the user's latest resume
    resume = (
        db.query(Resume)
        .filter(Resume.user_id == current_user)
        .order_by(Resume.id.desc())
        .first()
    )

    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="No resume found.",
        )

    additions = (
        db.query(ResumeSkillAddition)
        .filter(
            ResumeSkillAddition.user_id == current_user,
            ResumeSkillAddition.resume_id == resume.id,
            ResumeSkillAddition.is_approved == True,
        )
        .order_by(ResumeSkillAddition.id.asc())
        .all()
    )

    return {
        "resume_id": resume.id,
        "approved_additions": [
            {
                "id": item.id,
                "skill": item.skill,
                "evidence_level": item.evidence_level,
                "suggestion_text": item.suggestion_text,
                "source_task_ids": item.source_task_ids or [],
            }
            for item in additions
        ],
    }