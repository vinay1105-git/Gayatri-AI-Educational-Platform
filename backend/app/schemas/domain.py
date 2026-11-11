from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    cohort: str = Field(default="Fall 2026 - AI Engineering", max_length=80)
    program_track: str = Field(default="Applied Artificial Intelligence", max_length=100)


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: str
    avatar_initials: str
    department: str
    student_profile_id: Optional[int] = None
    student_code: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserSummary


class ResourceInteractionRequest(BaseModel):
    status: Literal["viewed", "bookmarked", "completed"]
    rating: Optional[int] = Field(default=None, ge=1, le=5)


class TelemetryCheckinRequest(BaseModel):
    study_hours: float = Field(ge=0.5, le=60.0)
    sessions_count: int = Field(ge=1, le=30)
    assignments_completed: int = Field(default=1, ge=0, le=15)
    notes: Optional[str] = Field(default=None, max_length=300)


class AssessmentSubmitRequest(BaseModel):
    answers: Dict[int, int]
    time_spent_seconds: int = Field(default=300, ge=5, le=10800)


class CreateQuestionInput(BaseModel):
    concept_id: int
    prompt: str = Field(min_length=10, max_length=1000)
    options: List[str] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    explanation: str = Field(min_length=8, max_length=1000)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    points: float = Field(default=20.0, ge=1.0, le=100.0)


class CreateAssessmentRequest(BaseModel):
    course_id: int
    title: str = Field(min_length=4, max_length=200)
    assessment_type: str = Field(default="Module Exam", max_length=48)
    description: str = Field(min_length=8, max_length=1000)
    duration_minutes: int = Field(default=20, ge=5, le=180)
    passing_score: float = Field(default=70.0, ge=30.0, le=95.0)
    questions: List[CreateQuestionInput] = Field(min_length=1, max_length=30)


class AssistantQueryRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1500)
    session_id: str = Field(default="default", min_length=1, max_length=64)


class InterventionCreateRequest(BaseModel):
    student_id: int
    intervention_type: str = Field(min_length=3, max_length=80)
    priority: Literal["low", "medium", "high"] = "medium"
    notes: str = Field(min_length=5, max_length=1000)


class InterventionUpdateRequest(BaseModel):
    status: Literal["open", "in_progress", "resolved"]
    notes: Optional[str] = Field(default=None, max_length=1000)
