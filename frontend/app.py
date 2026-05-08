from __future__ import annotations

import html
import os
from typing import Any

import requests
import streamlit as st


st.set_page_config(page_title="Resume Analyzer", page_icon=":page_facing_up:", layout="wide")

DEFAULT_API_BASE_URL = "https://ai-resume-jd-matcher-xmz7.onrender.com"
REQUEST_TIMEOUT_SECONDS = 240


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


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=DM+Sans:wght@400;500;700&display=swap');

        :root {
            --brand-blue: #1f63ff;
            --brand-cyan: #00b8d9;
            --brand-orange: #ff8a00;
            --brand-rose: #f03e8a;
            --bg-soft: #f4f8ff;
            --ink-strong: #12233d;
            --ink-muted: #4f5f77;
            --card-bg: rgba(255, 255, 255, 0.82);
            --card-border: rgba(31, 99, 255, 0.12);
            --card-shadow: rgba(17, 58, 150, 0.08);
            --metric-border: rgba(31, 99, 255, 0.14);
            --metric-bg: rgba(255, 255, 255, 0.82);
            --surface-soft: rgba(255, 255, 255, 0.7);
            --input-bg: rgba(255, 255, 255, 0.9);
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --brand-blue: #5d8dff;
                --brand-cyan: #36d4e8;
                --brand-orange: #ffb155;
                --brand-rose: #ff79b8;
                --bg-soft: #0f1829;
                --ink-strong: #e8f0ff;
                --ink-muted: #9fb2d7;
                --card-bg: rgba(19, 32, 56, 0.72);
                --card-border: rgba(122, 154, 255, 0.26);
                --card-shadow: rgba(0, 0, 0, 0.34);
                --metric-border: rgba(122, 154, 255, 0.28);
                --metric-bg: rgba(17, 30, 52, 0.78);
                --surface-soft: rgba(19, 32, 56, 0.58);
                --input-bg: rgba(12, 23, 41, 0.82);
            }
        }

        .stApp {
            font-family: 'DM Sans', sans-serif;
            color: var(--ink-strong);
            background:
                radial-gradient(900px 420px at -10% -20%, #c9dcff 0%, transparent 60%),
                radial-gradient(700px 360px at 105% 0%, #ffd7bd 0%, transparent 60%),
                radial-gradient(780px 380px at 50% 120%, #d7f6ff 0%, transparent 60%),
                var(--bg-soft);
        }

        @media (prefers-color-scheme: dark) {
            .stApp {
                background:
                    radial-gradient(900px 420px at -10% -20%, rgba(61, 98, 176, 0.45) 0%, transparent 60%),
                    radial-gradient(700px 360px at 105% 0%, rgba(138, 90, 31, 0.36) 0%, transparent 60%),
                    radial-gradient(780px 380px at 50% 120%, rgba(30, 126, 142, 0.28) 0%, transparent 60%),
                    var(--bg-soft);
            }
        }

        h1, h2, h3 {
            font-family: 'Space Grotesk', sans-serif !important;
            letter-spacing: -0.02em;
            color: var(--ink-strong) !important;
        }

        h4 {
            color: var(--ink-strong) !important;
        }

        .stMarkdown {
            color: var(--ink-strong) !important;
        }

        .stWrite {
            color: var(--ink-strong) !important;
        }

        .stCaption {
            color: var(--ink-muted) !important;
        }

        .stSubheader {
            color: var(--ink-strong) !important;
        }

        [data-testid="stSpinner"] {
            color: var(--brand-blue) !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            box-shadow: 0 10px 30px var(--card-shadow);
            padding: 0.35rem 0.4rem;
        }

        .hero-panel {
            background: linear-gradient(120deg, rgba(31, 99, 255, 0.96), rgba(0, 184, 217, 0.92));
            border-radius: 18px;
            padding: 1rem 1.2rem;
            color: #ffffff;
            box-shadow: 0 16px 34px rgba(20, 60, 150, 0.24);
            margin-bottom: 0.9rem;
        }

        @media (prefers-color-scheme: dark) {
            .hero-panel {
                background: linear-gradient(120deg, rgba(93, 141, 255, 0.88), rgba(54, 212, 232, 0.84));
                box-shadow: 0 16px 34px rgba(30, 80, 150, 0.36);
            }
        }

        .hero-panel p {
            margin: 0.25rem 0;
            opacity: 0.96;
        }

        .feature-chip {
            display: inline-block;
            margin: 0.2rem 0.35rem 0.2rem 0;
            padding: 0.3rem 0.62rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.24);
            border: 1px solid rgba(255, 255, 255, 0.36);
            font-size: 0.82rem;
            font-weight: 600;
        }

        @media (prefers-color-scheme: dark) {
            .feature-chip {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.22);
            }
        }

        .badge-wrap {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin-top: 0.2rem;
        }

        .badge-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.25rem 0.64rem;
            border: 1px solid transparent;
            font-size: 0.83rem;
            font-weight: 600;
            line-height: 1.2;
        }

        .badge-pill.b1 { background: #e4eeff; color: #123c8f; border-color: #bfd2ff; }
        .badge-pill.b2 { background: #dff9ff; color: #00667a; border-color: #aae9f6; }
        .badge-pill.b3 { background: #ffe9d5; color: #8a4200; border-color: #ffd2aa; }
        .badge-pill.b4 { background: #ffe1ef; color: #8a1852; border-color: #ffc2df; }

        @media (prefers-color-scheme: dark) {
            .badge-pill.b1 { background: rgba(76, 120, 220, 0.26); color: #cfe0ff; border-color: rgba(145, 173, 245, 0.45); }
            .badge-pill.b2 { background: rgba(25, 140, 163, 0.28); color: #c7f5ff; border-color: rgba(101, 209, 229, 0.44); }
            .badge-pill.b3 { background: rgba(165, 112, 39, 0.3); color: #ffe4c4; border-color: rgba(255, 190, 109, 0.44); }
            .badge-pill.b4 { background: rgba(159, 58, 108, 0.28); color: #ffd9ef; border-color: rgba(242, 140, 193, 0.44); }
        }

        .stButton > button {
            border-radius: 12px;
            border: 0;
            font-weight: 700;
            color: #ffffff;
            background: linear-gradient(100deg, var(--brand-blue), var(--brand-cyan));
            box-shadow: 0 10px 22px rgba(31, 99, 255, 0.26);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 14px 26px rgba(31, 99, 255, 0.3);
        }

        @media (prefers-color-scheme: dark) {
            .stButton > button {
                box-shadow: 0 10px 22px rgba(93, 141, 255, 0.3);
            }

            .stButton > button:hover {
                box-shadow: 0 14px 26px rgba(93, 141, 255, 0.4);
            }
        }

        [data-testid="metric-container"] {
            background: var(--metric-bg);
            border: 1px solid var(--metric-border);
            border-radius: 14px;
            padding: 0.45rem 0.75rem;
            box-shadow: 0 8px 24px var(--card-shadow);
        }

        [data-testid="stTextArea"] textarea,
        [data-testid="stFileUploaderDropzone"] {
            background: var(--input-bg) !important;
            border: 1px solid var(--card-border) !important;
        }

        [data-testid="stTextArea"] textarea {
            color: var(--ink-strong) !important;
        }

        [data-testid="stTextInput"] input {
            background: var(--input-bg) !important;
            border: 1px solid var(--card-border) !important;
            color: var(--ink-strong) !important;
        }

        [data-testid="stAlert"] {
            border-radius: 12px;
            background: var(--card-bg) !important;
            border: 1px solid var(--card-border) !important;
        }

        .stWarning {
            background: linear-gradient(135deg, rgba(255, 152, 0, 0.08), rgba(255, 187, 0, 0.06)) !important;
            border: 1px solid rgba(255, 152, 0, 0.24) !important;
        }

        @media (prefers-color-scheme: dark) {
            .stWarning {
                background: linear-gradient(135deg, rgba(255, 152, 0, 0.14), rgba(255, 187, 0, 0.1)) !important;
                border: 1px solid rgba(255, 187, 0, 0.36) !important;
            }
        }

        .stError {
            background: linear-gradient(135deg, rgba(244, 67, 54, 0.08), rgba(229, 57, 53, 0.06)) !important;
            border: 1px solid rgba(244, 67, 54, 0.24) !important;
        }

        @media (prefers-color-scheme: dark) {
            .stError {
                background: linear-gradient(135deg, rgba(244, 67, 54, 0.14), rgba(229, 57, 53, 0.1)) !important;
                border: 1px solid rgba(244, 67, 54, 0.36) !important;
            }
        }

        .stSuccess {
            background: linear-gradient(135deg, rgba(76, 175, 80, 0.08), rgba(56, 142, 60, 0.06)) !important;
            border: 1px solid rgba(76, 175, 80, 0.24) !important;
        }

        @media (prefers-color-scheme: dark) {
            .stSuccess {
                background: linear-gradient(135deg, rgba(76, 175, 80, 0.14), rgba(56, 142, 60, 0.1)) !important;
                border: 1px solid rgba(76, 175, 80, 0.36) !important;
            }
        }

        .stInfo {
            background: linear-gradient(135deg, rgba(33, 150, 243, 0.08), rgba(25, 118, 210, 0.06)) !important;
            border: 1px solid rgba(33, 150, 243, 0.24) !important;
        }

        @media (prefers-color-scheme: dark) {
            .stInfo {
                background: linear-gradient(135deg, rgba(33, 150, 243, 0.14), rgba(25, 118, 210, 0.1)) !important;
                border: 1px solid rgba(33, 150, 243, 0.36) !important;
            }
        }

        .info-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.7rem;
            margin-top: 0.35rem;
        }

        .info-card {
            background: var(--surface-soft);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 0.75rem 0.82rem;
            box-shadow: 0 6px 16px var(--card-shadow);
        }

        .info-card h4 {
            margin: 0 0 0.25rem 0;
            font-size: 0.96rem;
            font-family: 'Space Grotesk', sans-serif;
            color: var(--ink-strong) !important;
        }

        .info-card p {
            margin: 0;
            font-size: 0.86rem;
            color: var(--ink-muted);
            line-height: 1.35;
        }

        @media (max-width: 900px) {
            .info-grid {
                grid-template-columns: 1fr;
            }
        }

        .stCaption {
            color: var(--ink-muted) !important;
        }

        hr {
            border: 1px solid var(--card-border) !important;
        }

        [data-testid="stDivider"] {
            background: var(--card-border) !important;
        }

        .stColumn {
            background: transparent !important;
        }

        [data-testid="column"] {
            background: transparent !important;
        }

        /* Spinner styling */
        [data-testid="stSpinner"] svg {
            color: var(--brand-blue) !important;
        }

        /* Improve link colors */
        a {
            color: var(--brand-blue) !important;
        }

        @media (prefers-color-scheme: dark) {
            a {
                color: var(--brand-cyan) !important;
            }
        }

        /* File uploader area */
        [data-testid="stFileUploaderDropzone"] {
            transition: all 0.2s ease;
        }

        [data-testid="stFileUploaderDropzone"]:hover {
            border-color: var(--brand-blue) !important;
            background: var(--surface-soft) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def set_page(page: str) -> None:
    st.session_state.page = page


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
    chips: list[str] = []
    for idx, item in enumerate(items):
        variant = (idx % 4) + 1
        chips.append(f'<span class="badge-pill b{variant}">{html.escape(item)}</span>')
    st.markdown(f'<div class="badge-wrap">{"".join(chips)}</div>', unsafe_allow_html=True)


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


def render_projects(items: list[dict[str, str]]) -> None:
    if not items:
        st.write("No projects extracted.")
        return
    for item in items:
        title = item.get("title", "").strip()
        description = item.get("description", "").strip()
        technologies = item.get("technologies", "").strip()
        st.write(f"**{title or 'Project'}**")
        if description:
            st.write(description)
        if technologies:
            st.caption(f"Tech: {technologies}")


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

    st.subheader("Suitable Career Fields")
    render_badge_list(result.get("suitable_fields", []), "No career fields identified.")

    st.subheader("Education")
    render_education(result.get("education", []))

    st.subheader("Experience")
    render_experience(result.get("experience", []))

    st.subheader("Projects")
    render_projects(result.get("projects", []))

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


if "page" not in st.session_state:
    st.session_state.page = "home"

inject_theme()

st.title("AI Resume Analyzer & JD Matcher")
st.caption("Internal hiring workflow for resume screening and JD matching.")

if st.session_state.page == "home":
    st.markdown(
        """
        <div class="hero-panel">
            <h3 style="margin:0; color:#fff;">Welcome</h3>
            <p>Analyze resumes, validate document quality, and compare candidates with job descriptions in one flow.</p>
            <div>
                <span class="feature-chip">Resume Summary</span>
                <span class="feature-chip">Skill Extraction</span>
                <span class="feature-chip">Projects & Fields</span>
                <span class="feature-chip">JD Match Score</span>
            </div>
        </div>

        <div class="info-grid">
            <div class="info-card">
                <h4>What You Get</h4>
                <p>Summary, skills, education, experience, projects, and suitable career fields from each resume.</p>
            </div>
            <div class="info-card">
                <h4>JD Matching</h4>
                <p>Match score, fit classification, missing skills, and relevant experience highlights for quick screening.</p>
            </div>
            <div class="info-card">
                <h4>Supported Files</h4>
                <p>PDF and DOCX uploads are supported for both resume and JD. Text JD input is also available.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### How To Use")
    st.write("1. Pick an analysis mode using one of the buttons below.")
    st.write("2. Upload a resume (PDF or DOCX).")
    st.write("3. For matching, add JD text or upload a JD file.")
    st.write("4. Click Analyze to view extracted insights and timing metrics.")

    col1, col2 = st.columns(2)
    with col1:
        st.button(
            "Open Resume Analysis",
            type="primary",
            use_container_width=True,
            on_click=set_page,
            args=("resume",),
        )
    with col2:
        st.button(
            "Open Resume vs JD Match",
            use_container_width=True,
            on_click=set_page,
            args=("match",),
        )

else:
    st.button("Back to Home", on_click=set_page, args=("home",))

    mode = "Resume Analysis" if st.session_state.page == "resume" else "Resume vs JD Match"

    resume_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])
    jd_text = ""
    jd_file = None

    if mode == "Resume vs JD Match":
        jd_text = st.text_area("Job Description Text", height=180, placeholder="Paste the job description here...")
        jd_file = st.file_uploader("Or Upload JD File", type=["pdf", "docx"], key="jd_file")
        st.caption("Use pasted JD text, a JD PDF/DOCX file, or both. Pasted text is used first when provided.")

    run_clicked = st.button("Analyze", type="primary", use_container_width=True)

    if run_clicked:
        backend_ok, backend_message = check_backend_health()
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
                        "The backend is still processing a large file. "
                        "Please wait a bit longer and rerun if needed."
                    )
                except requests.ConnectionError:
                    st.error("Unable to connect to the backend service.")
                except requests.RequestException as exc:
                    st.error(f"Backend request failed: {exc}")
