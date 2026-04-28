# AI Resume Analyzer & JD Matcher

FastAPI backend plus Streamlit frontend for resume analysis and resume-vs-JD matching. The app is designed around the PRD and user stories: it only shows the required summary and screening outputs, with a resume-only mode and a JD match mode.

## Features
- Upload `PDF` or `DOCX` resumes
- Upload `PDF` or `DOCX` job descriptions or paste JD text
- Extract and normalize resume text locally
- Generate resume-only analysis:
  - Professional summary
  - Skills
  - Education
  - Experience
- Generate resume vs JD match output:
  - Match score
  - Missing skills
  - Matching skills
  - Relevant experience highlights
  - Fit classification
- Use a single OpenRouter request per analysis for faster turnaround

## Project Structure
- `backend/app/main.py`: FastAPI application and endpoints
- `backend/app/extractors.py`: PDF and DOCX parsing
- `backend/app/openrouter.py`: OpenRouter client and prompt construction
- `backend/app/analysis.py`: response normalization and deterministic post-processing
- `frontend/app.py`: Streamlit interface
- `tests/test_match_utils.py`: unit tests for normalization and classification rules

## Environment Variables
Copy `.env.example` to `.env` and fill in your values.

- `OPENROUTER_API_KEY`: required for analysis calls
- `OPENROUTER_MODEL`: optional model override
- `OPENROUTER_TIMEOUT_SECONDS`: request timeout for OpenRouter
- `TOTAL_REQUEST_BUDGET_SECONDS`: total backend processing budget, default `9.5`
- `OPENROUTER_MAX_RETRIES`: retry count for LLM requests, default `0`
- `RESUME_MAX_TOKENS`: resume analysis response budget, default `180`
- `MATCH_MAX_TOKENS`: JD match response budget, default `260`
- `MAX_RESUME_CHARS`: trim resume input before the LLM call, default `6000`
- `MAX_JD_CHARS`: trim JD input before the LLM call, default `3500`
- `API_BASE_URL`: FastAPI base URL used by Streamlit
- `GOOD_FIT_THRESHOLD`: default `80`
- `MODERATE_FIT_THRESHOLD`: default `60`

## Local Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env`:
```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openrouter/auto
OPENROUTER_TIMEOUT_SECONDS=4.5
TOTAL_REQUEST_BUDGET_SECONDS=9.5
OPENROUTER_MAX_RETRIES=0
RESUME_MAX_TOKENS=180
MATCH_MAX_TOKENS=260
MAX_RESUME_CHARS=6000
MAX_JD_CHARS=3500
API_BASE_URL=http://localhost:8000
GOOD_FIT_THRESHOLD=80
MODERATE_FIT_THRESHOLD=60
```

## Run the Backend
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

## Run the Frontend
```bash
streamlit run frontend/app.py
```

## API Endpoints
### `GET /health`
Returns service readiness and whether an OpenRouter key is configured.

### `POST /analyze/resume`
Multipart form-data:
- `resume`: PDF or DOCX file

Returns:
- `summary`
- `skills`
- `education`
- `experience`
- `warnings`

### `POST /analyze/match`
Multipart form-data:
- `resume`: PDF or DOCX file
- `jd_text`: optional job description text
- `jd_file`: optional job description PDF or DOCX file

Returns:
- `summary`
- `skills`
- `education`
- `experience`
- `jd_skills`
- `matching_skills`
- `missing_skills`
- `match_score`
- `fit_classification`
- `relevant_experience_highlights`
- `warnings`

## Performance Notes
- Text extraction happens locally before calling the LLM.
- Each analysis request sends exactly one structured prompt to OpenRouter.
- Resume and JD inputs are trimmed before the LLM call to reduce latency and improve the chance of finishing near the 10-second target.
- Each API response includes timing metadata so the UI can show total time, read time, extraction time, and LLM time.
- The backend now enforces a total request budget and caps the LLM timeout to the remaining time after file reading and extraction.
- The default LLM path now uses lower token budgets, zero retries, and a shorter timeout to reduce model wait time.
- Deterministic post-processing handles score clamping, deduplication, and fit classification.
- Keeping resumes to a typical single-candidate length and using a fast OpenRouter model will help keep analysis under 10 seconds.

## Error Handling
- Unsupported or corrupted files return clear validation errors.
- Empty JD input is blocked in the Streamlit UI.
- Backend/network failures are surfaced in the UI without crashing the app.

## Tests
Run:
```bash
pytest
```

The current tests verify text normalization, skill deduplication, score clamping, and fit classification edge cases.
