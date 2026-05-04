import pytest
from fastapi import HTTPException

from backend.app.extractors import validate_extension


def test_validate_extension_rejects_invalid_file_with_standard_message() -> None:
    """Test that any unsupported file type returns 'please upload required file'."""
    invalid_files = ["resume.txt", "jd.csv", "document.xlsx", "data.json"]
    
    for filename in invalid_files:
        with pytest.raises(HTTPException) as exc_info:
            validate_extension(filename, label="resume")
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "please upload required file"


def test_validate_extension_accepts_pdf() -> None:
    """Test that PDF files are accepted."""
    result = validate_extension("resume.pdf", label="resume")
    assert result == ".pdf"


def test_validate_extension_accepts_docx() -> None:
    """Test that DOCX files are accepted."""
    result = validate_extension("resume.docx", label="resume")
    assert result == ".docx"
