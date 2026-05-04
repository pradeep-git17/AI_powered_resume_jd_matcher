import pytest
from fastapi import HTTPException

from backend.app.extractors import _is_resume_content, _is_jd_content, _validate_content


def test_is_resume_content_detects_valid_resume() -> None:
    """Test that valid resume content is detected."""
    resume_text = """
    John Doe
    Email: john@example.com
    Phone: 555-1234
    
    Professional Summary:
    Experienced software engineer with skills in Python and JavaScript.
    
    Experience:
    Senior Engineer at Tech Company (2020-2024)
    - Led development of core features
    
    Skills:
    - Python, JavaScript, React, SQL
    
    Education:
    Bachelor's degree in Computer Science
    """
    assert _is_resume_content(resume_text) is True


def test_is_resume_content_rejects_invalid_content() -> None:
    """Test that non-resume content is rejected."""
    non_resume_text = "This is just a random PDF with some text about cooking recipes and food."
    assert _is_resume_content(non_resume_text) is False


def test_is_jd_content_detects_valid_jd() -> None:
    """Test that valid job description content is detected."""
    jd_text = """
    Job Description
    Position: Senior Software Engineer
    
    About the Role:
    We are looking for a talented engineer to join our team.
    
    Responsibilities:
    - Design and develop new features
    - Work with product teams
    
    Requirements:
    - 5+ years of experience
    - Strong skills in Python and JavaScript
    - Bachelor's degree in Computer Science or related field
    
    Qualifications:
    - Experience with cloud platforms
    """
    assert _is_jd_content(jd_text) is True


def test_is_jd_content_rejects_invalid_content() -> None:
    """Test that non-JD content is rejected."""
    non_jd_text = "This is just a random PDF with information about cooking and recipes."
    assert _is_jd_content(non_jd_text) is False


def test_validate_content_rejects_invalid_resume() -> None:
    """Test that invalid resume content raises HTTPException."""
    invalid_text = "This is a random document about cooking and food recipes."
    
    with pytest.raises(HTTPException) as exc_info:
        _validate_content(invalid_text, label="resume")
    
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "please upload required file"


def test_validate_content_rejects_invalid_jd() -> None:
    """Test that invalid JD content raises HTTPException."""
    invalid_text = "This is a random document about cooking and food recipes."
    
    with pytest.raises(HTTPException) as exc_info:
        _validate_content(invalid_text, label="job description")
    
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "please upload required file"


def test_validate_content_accepts_valid_resume() -> None:
    """Test that valid resume content passes validation."""
    valid_resume = """
    John Doe
    Professional Summary: Software engineer
    Experience: 5 years
    Skills: Python, JavaScript
    Education: Bachelor's degree
    """
    # Should not raise any exception
    _validate_content(valid_resume, label="resume")


def test_validate_content_accepts_valid_jd() -> None:
    """Test that valid JD content passes validation."""
    valid_jd = """
    Job Description
    Position: Engineer
    Responsibilities: Design systems
    Requirements: 5 years experience
    Qualifications: Bachelor's degree
    """
    # Should not raise any exception
    _validate_content(valid_jd, label="job description")
