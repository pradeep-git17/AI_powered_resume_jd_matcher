from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st


st.set_page_config(page_title="Resume Analyzer", page_icon=":page_facing_up:", layout="wide")

DEFAULT_API_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT_SECONDS = 35


def get_api_base_url() -> str:
    env_value = os.getenv("API_BASE_URL")
    if env_value:
        return env_value

    try:
        secret_value = st.secrets.get("API_BASE_URL")
        if secret_value:
            return str(secret_value)
    except Exception:
        pass

    return DEFAULT_API_BASE_URL


API_BASE_URL = get_api_base_url()


def check_backend_health() -> tuple[bool, str]:
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        payload = response.json()
        status = payload.get("status", "unknown")
        configured = payload.get("model_configured", False)
        return True, f"Backend connected | status: `{status}` | OpenRouter key configured: `{configured}`"
    except requests.Timeout:
        return False, "Backend health check timed out."
    except requests.ConnectionError:
        return False, "Could not connect to the backend service."
    except requests.RequestException as exc:
        return False, f"Backend health check failed: {exc}"


def post_resume_analysis(file_obj: Any) -> dict[str, Any]:
    files = {
        "resume": (file_obj.name, file_obj.getvalue(), file_obj.type or "application/octet-stream"),
    }
    response = requests.post(
        f"{API_BASE_URL}/analyze/resume",
        files=files,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def post_resume_match(file_obj: Any, jd_text: str) -> dict[str, Any]:
    return post_resume_match_with_jd_file(file_obj, jd_text, None)


def post_resume_match_with_jd_file(file_obj: Any, jd_text: str, jd_file_obj: Any | None) -> dict[str, Any]:
    files = {
        "resume": (file_obj.name, file_obj.getvalue(), file_obj.type or "application/octet-stream"),
    }
    if jd_file_obj is not None:
        files["jd_file"] = (
            jd_file_obj.name,
            jd_file_obj.getvalue(),
            jd_file_obj.type or "application/octet-stream",
        )
    data = {}
    if jd_text.strip():
        data["jd_text"] = jd_text
    response = requests.post(
        f"{API_BASE_URL}/analyze/match",
        files=files,
        data=data,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def render_badge_list(items: list[str], empty_message: str) -> None:
    if not items:
        st.write(empty_message)
        return
    st.write("  ".join(f"`{item}`" for item in items))


def render_education(items: list[dict[str, str]]) -> None:
    if not items:
        st.write("No education details extracted.")
        return
    for item in items:
        degree = item.get("degree", "").strip()
        institution = item.get("institution", "").strip()
        line = " - ".join(part for part in [degree, institution] if part)
        st.write(line or "Education detail unavailable")


def render_experience(items: list[dict[str, str]]) -> None:
    if not items:
        st.write("No experience details extracted.")
        return
    for item in items:
        role = item.get("role", "").strip()
        duration = item.get("duration", "").strip()
        highlights = item.get("highlights", "").strip()
        title = " | ".join(part for part in [role, duration] if part)
        st.write(f"**{title or 'Experience'}**")
        if highlights:
            st.write(highlights)


def render_results(result: dict[str, Any], mode: str) -> None:
    timing = result.get("timing", {})
    if timing:
        st.subheader("Response Timing")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", f"{timing.get('total_ms', 0)} ms")
            st.caption(f"Path: {timing.get('path', 'unknown')}")
        with col2:
            st.metric("Read + Extract", f"{timing.get('upload_read_ms', 0) + timing.get('extraction_ms', 0)} ms")
            st.caption(
                f"Read {timing.get('upload_read_ms', 0)} ms | Extract {timing.get('extraction_ms', 0)} ms"
            )
        with col3:
            model_time = timing.get("llm_ms", 0) or timing.get("fallback_ms", 0)
            label = "LLM" if timing.get("path") == "llm" else "Fallback"
            st.metric(label, f"{model_time} ms")

    st.subheader("Professional Summary")
    st.write(result.get("summary", "No summary generated."))

    st.subheader("Skills")
    render_badge_list(result.get("skills", []), "No skills extracted.")

    st.subheader("Education")
    render_education(result.get("education", []))

    st.subheader("Experience")
    render_experience(result.get("experience", []))

    if mode == "match":
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Match Score")
            st.metric(label="Score", value=f"{result.get('match_score', 0)}%")
        with col2:
            st.subheader("Fit Classification")
            st.write(result.get("fit_classification", "Not available"))

        st.subheader("Missing Skills")
        render_badge_list(result.get("missing_skills", []), "No missing skills identified.")

        st.subheader("Matching Skills")
        render_badge_list(result.get("matching_skills", []), "No matching skills identified.")

        st.subheader("Relevant Experience")
        highlights = result.get("relevant_experience_highlights", [])
        if highlights:
            for item in highlights:
                st.write(f"- {item}")
        else:
            st.write("No relevant experience highlights extracted.")

    warnings = result.get("warnings", [])
    if warnings:
        st.subheader("Warnings")
        for warning in warnings:
            st.warning(warning)


st.title("AI Resume Analyzer & JD Matcher")
st.caption("Internal hiring workflow for resume screening and JD matching.")

backend_ok, backend_message = check_backend_health()
if not backend_ok:
    st.error(backend_message)

mode = st.radio(
    "Select analysis mode",
    options=["Resume Analysis", "Resume vs JD Match"],
    horizontal=True,
)

resume_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])
jd_text = ""
jd_file = None

if mode == "Resume vs JD Match":
    jd_text = st.text_area("Job Description Text", height=180, placeholder="Paste the job description here...")
    jd_file = st.file_uploader("Or Upload JD File", type=["pdf", "docx"], key="jd_file")
    st.caption("Use pasted JD text, a JD PDF/DOCX file, or both. Pasted text is used first when provided.")

run_clicked = st.button("Analyze", type="primary", use_container_width=True)

if run_clicked:
    if resume_file is None:
        st.error("Please upload a resume file before running analysis.")
    elif mode == "Resume vs JD Match" and not jd_text.strip() and jd_file is None:
        st.error("Please enter job description text or upload a JD PDF/DOCX file.")
    elif not backend_ok:
        st.error("Backend is not reachable from Streamlit right now. Confirm FastAPI is still running.")
    else:
        with st.spinner("Analyzing resume with fast mode enabled..."):
            try:
                if mode == "Resume Analysis":
                    payload = post_resume_analysis(resume_file)
                    render_results(payload, mode="resume")
                else:
                    payload = post_resume_match_with_jd_file(resume_file, jd_text, jd_file)
                    render_results(payload, mode="match")
            except requests.HTTPError as exc:
                detail = "Unexpected backend error."
                try:
                    detail = exc.response.json().get("detail", detail)
                except Exception:
                    detail = exc.response.text or detail
                st.error(detail)
            except requests.Timeout:
                st.error(
                    "The backend request timed out. "
                    "This usually means file parsing or the OpenRouter response took too long. "
                    "Try a smaller PDF/DOCX, shorter JD text, or rerun once."
                )
            except requests.ConnectionError:
                st.error("Unable to connect to the backend service.")
            except requests.RequestException as exc:
                st.error(f"Backend request failed: {exc}")
