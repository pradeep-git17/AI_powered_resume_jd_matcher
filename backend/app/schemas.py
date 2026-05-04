from typing import Literal

from pydantic import BaseModel, Field


FitClassification = Literal["Good Fit", "Moderate Fit", "Low Fit"]


class EducationItem(BaseModel):
    degree: str = ""
    institution: str = ""


class ExperienceItem(BaseModel):
    role: str = ""
    duration: str = ""
    highlights: str = ""


class ProjectItem(BaseModel):
    title: str = ""
    description: str = ""
    technologies: str = ""


class TimingBreakdown(BaseModel):
    total_ms: int = 0
    upload_read_ms: int = 0
    extraction_ms: int = 0
    llm_ms: int = 0
    fallback_ms: int = 0
    path: str = ""


class ResumeAnalysisResult(BaseModel):
    summary: str
    skills: list[str] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    suitable_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    timing: TimingBreakdown = Field(default_factory=TimingBreakdown)


class ResumeMatchResult(ResumeAnalysisResult):
    jd_skills: list[str] = Field(default_factory=list)
    matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    match_score: int
    fit_classification: FitClassification
    relevant_experience_highlights: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    model_configured: bool
