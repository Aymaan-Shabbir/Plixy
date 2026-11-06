
import os
import html
import tempfile
import textwrap

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from dotenv import load_dotenv

from core.rag_engine import (
    ask_question,
    build_rag_chain,
    load_rag_chain,
)

from core.transcriber import transcribe_all

from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)

from core.summarize import summarize, generate_title
from utils.audio_processor import process_input
from utils.playlist_duration import calculate_playlist_duration


load_dotenv()


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Plixy | Meeting Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ==================================================
# SESSION STATE
# ==================================================

DEFAULT_STATE = {
    "meeting": None,
    "rag_chain": None,
    "chat_history": [],
    "playlist_result": None,
}

for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ==================================================
# HTML RENDERING
# ==================================================

def render_html(content):
    """
    Render raw HTML directly.

    IMPORTANT:
    Use st.html(), NOT st.markdown(), for custom HTML.
    This prevents Streamlit from interpreting HTML
    as a Markdown code block.
    """

    st.html(textwrap.dedent(content).strip())


# ==================================================
# CUSTOM CSS
# ==================================================


CSS = """
<style>

@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

:root {
    --bg: #F3F0E8;
    --surface: #FFFFFF;
    --black: #111111;
    --orange: #FF5A1F;
    --muted: #555555;
}

/* GLOBAL */

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--black) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

[data-testid="stHeader"] {
    background: var(--bg) !important;
}

.block-container {
    max-width: 1350px !important;
    padding: 3rem 4rem 5rem !important;
}

/* BRAND */

.brand {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(4rem, 9vw, 7rem);
    font-weight: 700;
    font-style: italic;
    letter-spacing: -7px;
    line-height: 1.12;
    padding-top: 0.08em;
    color: var(--black);
}

.brand-dot {
    color: var(--orange);
}

.tagline {
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 2px;
    margin-top: 15px;
    color: var(--black);
}

/* HEADER ALIGNMENT */

.header-wrap {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    gap: 30px;
    padding: 10px 0 25px 0;
}

.header-brand {
    flex: 1;
    min-width: 0;
}

.top-meta {
    flex: 0 0 auto;
    text-align: right;
    font-family: 'Space Mono', monospace;
    font-size: 0.78rem;
    font-weight: 700;
    line-height: 2;
    letter-spacing: 1px;
    color: #111111;
    white-space: nowrap;
    padding: 5px 0;
    margin: 0;
}

/* HERO */

.hero {
    margin-top: 55px;
    margin-bottom: 45px;
}

.hero-title {
    font-size: clamp(3rem, 8vw, 6.5rem);
    font-weight: 700;
    letter-spacing: -5px;
    line-height: 0.98;
    margin-top: 18px;
    color: var(--black);
}

.hero-title span {
    color: var(--orange);
}

.hero-copy {
    font-size: 1.1rem;
    font-weight: 500;
    max-width: 650px;
    margin-top: 25px;
    line-height: 1.6;
    color: var(--muted);
}

/* SECTION TYPOGRAPHY */

.section-heading {
    font-size: clamp(2rem, 4vw, 3rem);
    font-weight: 700;
    letter-spacing: -1.8px;
    line-height: 1.1;
    margin-bottom: 12px;
}

.section-caption {
    font-size: 1.05rem;
    font-weight: 500;
    color: var(--muted);
    margin-bottom: 25px;
}

.eyebrow {
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: var(--orange);
    margin-bottom: 12px;
}

/* CARDS */

.brutal-card {
    background: var(--surface);
    border: 3px solid var(--black);
    padding: 30px;
    box-shadow: 8px 8px 0 var(--black);
    margin-bottom: 28px;
}

.orange-card {
    background: var(--orange);
    border: 3px solid var(--black);
    padding: 30px;
    box-shadow: 8px 8px 0 var(--black);
    color: var(--black);
    margin-bottom: 30px;
    overflow-wrap: anywhere;
}

.stat-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 1px;
}

.stat-value {
    font-size: clamp(2.5rem, 5vw, 4rem);
    font-weight: 700;
    letter-spacing: -2px;
}

/* INPUT LABELS */

[data-testid="stWidgetLabel"] p,
.stRadio label p,
.stCheckbox label p {
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    color: var(--black) !important;
}

/* INPUTS */

.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
[data-testid="stChatInput"] textarea {
    background: #FFFFFF !important;
    color: #111111 !important;
    border: 3px solid #111111 !important;
    border-radius: 0 !important;
    min-height: 58px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    padding: 12px 16px !important;
    box-shadow: 4px 4px 0 #111111 !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder,
[data-testid="stChatInput"] textarea::placeholder {
    color: #686868 !important;
    opacity: 1 !important;
    font-weight: 500 !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus {
    border-color: var(--orange) !important;
    box-shadow: 5px 5px 0 var(--orange) !important;
}

/* SELECTBOX */

div[data-baseweb="select"] > div {
    background: #FFFFFF !important;
    border: 3px solid #111111 !important;
    border-radius: 0 !important;
    min-height: 58px !important;
    box-shadow: 4px 4px 0 #111111 !important;
}

div[data-baseweb="select"] * {
    color: #111111 !important;
    font-weight: 600 !important;
}

/* RADIO */

div[role="radiogroup"] {
    gap: 15px !important;
}

div[role="radiogroup"] label {
    font-weight: 700 !important;
}

div[role="radiogroup"] label > div:first-child {
    border-color: #111111 !important;
}

/* BUTTONS */

.stButton > button,
.stFormSubmitButton > button {
    min-height: 62px !important;
    background: #111111 !important;
    color: #FFFFFF !important;
    border: 3px solid #111111 !important;
    border-radius: 0 !important;
    box-shadow: 5px 5px 0 var(--orange) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    transition: 0.15s ease !important;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: var(--orange) !important;
    color: #111111 !important;
    border-color: #111111 !important;
    box-shadow: 2px 2px 0 #111111 !important;
    transform: translate(3px, 3px) !important;
}

/* TABS */

.stTabs [data-baseweb="tab-list"] {
    gap: 12px;
    border-bottom: 3px solid #111111;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 0 !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    padding: 15px 20px !important;
}

.stTabs [aria-selected="true"] {
    color: var(--orange) !important;
    border-bottom: 5px solid var(--orange) !important;
}

/* CONTAINERS */

[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border: 3px solid #111111 !important;
    border-radius: 0 !important;
    box-shadow: 7px 7px 0 #111111 !important;
    padding: 20px !important;
}

/* FILE UPLOADER */

[data-testid="stFileUploader"] {
    background: #FFFFFF !important;
    border: 3px dashed #111111 !important;
    border-radius: 0 !important;
    padding: 18px !important;
}

[data-testid="stFileUploader"] button {
    border: 2px solid #111111 !important;
    border-radius: 0 !important;
    font-weight: 700 !important;
}

/* CHAT */

[data-testid="stChatMessage"] {
    background: #FFFFFF !important;
    border: 2px solid #111111 !important;
    border-radius: 0 !important;
    padding: 20px !important;
    margin-bottom: 15px !important;
    color: #111111 !important;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] strong,
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3 {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
    opacity: 1 !important;
}

[data-testid="stChatInput"] {
    border-radius: 0 !important;
}

[data-testid="stChatInput"] textarea {
    background: #FFFFFF !important;
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}
/* FIRST-RUN MODEL NOTICE */

.model-notice {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    background: #FFF0E8;
    border: 2px solid #111111;
    border-left: 7px solid #FF5A1F;
    padding: 20px 24px;
    margin: 25px 0;
    box-shadow: 5px 5px 0 #111111;
}

.notice-icon {
    font-size: 1.5rem;
    line-height: 1.3;
}

.notice-content {
    flex: 1;
}

.notice-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 1px;
    color: #111111;
    margin-bottom: 8px;
}

.notice-text {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.95rem;
    line-height: 1.65;
    font-weight: 500;
    color: #333333;
}

.notice-highlight {
    color: #FF5A1F;
    font-weight: 700;
}

@media (max-width: 600px) {
    .model-notice {
        padding: 16px;
        gap: 10px;
    }

    .notice-text {
        font-size: 0.88rem;
    }
}

/* EXPANDERS */

[data-testid="stExpander"] {
    background: #FFFFFF !important;
    border: 2px solid #111111 !important;
    border-radius: 0 !important;
}

/* PROGRESS */

.stProgress > div {
    background: #DDDBD4 !important;
    border: 2px solid #111111 !important;
    border-radius: 0 !important;
    height: 18px !important;
}

.stProgress > div > div > div > div {
    background: var(--orange) !important;
}

/* DIVIDERS */

hr {
    border: 0 !important;
    border-top: 3px solid #111111 !important;
    margin: 40px 0 !important;
}

/* FOOTER */

.footer {
    text-align: center;
    padding: 35px 0 20px 0;
}

.footer-brand {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.8rem;
    font-weight: 700;
    font-style: italic;
    letter-spacing: -3px;
    color: var(--black);
    line-height: 1;
}

.footer-credit {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 1px;
    margin-top: 15px;
    color: var(--black);
}

.footer-powered {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    margin-top: 8px;
    color: var(--muted);
}

/* MOBILE */

@media (max-width: 768px) {

    .block-container {
        padding: 2.25rem 1.2rem 3rem !important;
    }

    .brand {
        font-size: clamp(3rem, 12vw, 4.2rem);
        line-height: 1.15;
        padding-top: 0.08em;
        letter-spacing: -4px;
    }

    .header-wrap {
        flex-direction: column;
        align-items: flex-start;
        gap: 18px;
    }

    .top-meta {
        text-align: left;
        white-space: normal;
        font-size: 0.7rem;
        margin-top: 0;
    }

    .tagline {
        font-size: 0.68rem;
        letter-spacing: 1px;
    }

    .hero {
        margin-top: 35px;
    }

    .hero-title {
        font-size: clamp(3rem, 12vw, 5rem);
        letter-spacing: -3px;
    }

    .hero-copy {
        font-size: 1rem;
    }

    .section-heading {
        font-size: 2rem;
    }

    .section-caption {
        font-size: 0.95rem;
    }

    .brutal-card,
    .orange-card {
        padding: 20px;
        box-shadow: 5px 5px 0 #111111;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        width: 100%;
        min-height: 58px !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        overflow-x: auto;
        flex-wrap: nowrap;
    }

    .stTabs [data-baseweb="tab"] {
        white-space: nowrap;
        padding: 12px !important;
    }
}

@media (max-width: 480px) {

    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    .brand {
        font-size: clamp(3rem, 12vw, 3.5rem);
        line-height: 1.15;
        padding-top: 0.08em;
    }

    .hero-title {
        font-size: 3rem;
        letter-spacing: -2px;
    }

    .brutal-card,
    .orange-card {
        padding: 16px;
        box-shadow: 4px 4px 0 #111111;
    }

    .section-heading {
        font-size: 1.8rem;
    }

    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea {
        font-size: 1rem !important;
        min-height: 55px !important;
    }
}

</style>
"""

st.html(CSS)

# CSS also goes through st.html().
st.html(textwrap.dedent(CSS))


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def format_duration(seconds):

    seconds = max(0, int(seconds))

    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []

    if days:
        parts.append(f"{days}d")

    if hours:
        parts.append(f"{hours}h")

    if minutes:
        parts.append(f"{minutes}m")

    if seconds:
        parts.append(f"{seconds}s")

    return " ".join(parts) if parts else "0s"


def estimate_processing_time(source_type, uploaded_file=None):

    """
    Approximate processing time.

    This is a countdown estimate, not an exact prediction.
    """

    if source_type == "upload" and uploaded_file is not None:

        file_size_mb = uploaded_file.size / (1024 * 1024)

        estimated_seconds = 120 + (file_size_mb * 5)

    else:

        estimated_seconds = 240

    return int(max(120, min(estimated_seconds, 1800)))


# ==================================================
# COUNTDOWN TIMER
# ==================================================

def render_countdown(seconds):

    """
    Browser-side countdown.

    Runs independently while Python waits for
    transcription and LLM responses.
    """

    countdown_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>

            body {{
                margin: 0;
                padding: 0;
                background: transparent;
                font-family: Arial, sans-serif;
                color: #111111;
            }}

            .timer-card {{
                background: #FFFFFF;
                border: 3px solid #111111;
                box-shadow: 5px 5px 0 #111111;
                padding: 16px 20px;
            }}

            .timer-label {{
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 2px;
                color: #555555;
                margin-bottom: 8px;
            }}

            .timer-value {{
                font-size: 34px;
                font-weight: 800;
                letter-spacing: -1px;
            }}

            .timer-message {{
                font-size: 12px;
                margin-top: 8px;
                font-weight: 600;
                color: #555555;
            }}

            .timer-track {{
                height: 9px;
                background: #E5E2DA;
                border: 2px solid #111111;
                margin-top: 14px;
            }}

            .timer-fill {{
                height: 100%;
                width: 100%;
                background: #FF5A1F;
                transition: width 1s linear;
            }}

        </style>
    </head>

    <body>

        <div class="timer-card">

            <div class="timer-label">
                ESTIMATED TIME REMAINING
            </div>

            <div class="timer-value" id="timer">
                --:--
            </div>

            <div class="timer-message" id="timer-message">
                Plixy is working on your meeting...
            </div>

            <div class="timer-track">
                <div class="timer-fill" id="timer-fill"></div>
            </div>

        </div>

        <script>

            let remaining = {seconds};
            const total = {seconds};

            const timer = document.getElementById("timer");
            const message = document.getElementById("timer-message");
            const fill = document.getElementById("timer-fill");

            function formatTime(value) {{

                const mins = Math.floor(value / 60);
                const secs = value % 60;

                return String(mins).padStart(2, "0")
                    + ":"
                    + String(secs).padStart(2, "0");
            }}

            function updateTimer() {{

                timer.textContent = formatTime(remaining);

                const percentage = Math.max(
                    0,
                    (remaining / total) * 100
                );

                fill.style.width = percentage + "%";

                if (remaining > 0) {{

                    remaining--;

                }} else {{

                    timer.textContent = "00:00";

                    message.textContent =
                        "Taking longer than estimated. Still processing...";

                    fill.style.width = "0%";
                }}
            }}

            updateTimer();

            const interval = setInterval(() => {{

                if (remaining > 0) {{

                    updateTimer();

                }} else {{

                    clearInterval(interval);
                }}

            }}, 1000);

        </script>

    </body>
    </html>
    """

    components.html(
        countdown_html,
        height=125,
        scrolling=False,
    )


# ==================================================
# MEETING PIPELINE
# ==================================================

def run_pipeline(
    source,
    language,
    is_new_meeting,
    progress_callback=None,
):

    def update_progress(value, message):

        if progress_callback:
            progress_callback(value, message)

    update_progress(0.05, "Preparing audio...")

    chunks = process_input(source)

    update_progress(0.25, "Transcribing audio...")

    transcript = transcribe_all(chunks, language)

    if not transcript or not transcript.strip():

        raise ValueError("No transcript was generated.")

    update_progress(0.45, "Generating meeting title...")

    title = generate_title(transcript)

    update_progress(0.55, "Generating summary...")

    meeting_summary = summarize(transcript)

    update_progress(0.65, "Extracting action items...")

    action_items = extract_action_items(transcript)

    update_progress(0.75, "Extracting key decisions...")

    decisions = extract_key_decisions(transcript)

    update_progress(0.85, "Extracting open questions...")

    questions = extract_questions(transcript)

    update_progress(0.92, "Preparing meeting intelligence...")

    if is_new_meeting:

        rag_chain = build_rag_chain(transcript)

    else:

        rag_chain = load_rag_chain()

    update_progress(1.0, "Meeting processing complete!")

    return {
        "title": title,
        "transcript": transcript,
        "summary": meeting_summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }


# ==================================================
# HEADER
# ==================================================

render_html(
    """
    <div class="header-wrap">

        <div class="header-brand">
            <div class="brand">
                Plixy<span class="brand-dot">.</span>
            </div>

            <div class="tagline">
                MEETING INTELLIGENCE / BUILT FOR THINKERS
            </div>
        </div>

        <div class="top-meta">
            MADE BY AYMAAN SHABBIR<br>
            POWERED BY MISTRAL AI<br>
            VERSION 1.0 / 2026
        </div>

    </div>
    """
)


# ==================================================
# HERO
# ==================================================

st.markdown("---")

render_html(
    """
    <div class="hero">

        <div class="eyebrow">
            YOUR AI WORKSPACE / 001
        </div>

        <div class="hero-title">
            Less listening.<br>
            More <span>thinking.</span>
        </div>

        <p class="hero-copy">
            Turn conversations into structured knowledge.
            Extract decisions, identify action items and
            chat with your meetings.
        </p>

    </div>
    """
)


# ==================================================
# SECTION 01 - MEETING PROCESSOR
# ==================================================

st.markdown("---")

render_html(
    """
    <div class="eyebrow">
        01 / MEETING INTELLIGENCE
    </div>

    <div class="section-heading">
        Process a meeting.
    </div>

    <div class="section-caption">
        Upload a recording or provide a YouTube video URL.
    </div>
    """
)

render_html(
    """
    <div class="model-notice">

        <div class="notice-icon">⚡</div>

        <div class="notice-content">

            <div class="notice-title">
                FIRST-TIME SETUP / MODEL INITIALIZATION
            </div>

            <div class="notice-text">
                Running Plixy for the first time may require
                downloading and initializing the transcription
                model locally on your device.

                <br><br>

                This process may take a few minutes depending on
                your <span class="notice-highlight">
                internet speed, device specifications, available
                RAM and CPU/GPU performance.</span>

                Subsequent runs may be faster because the model
                files are cached locally.
            </div>

        </div>

    </div>
    """
)

with st.container(border=True):

    input_method = st.radio(
        "Choose your input method",
        ["YouTube URL", "Upload local file"],
        horizontal=True,
    )

    source_url = ""
    uploaded_file = None

    if input_method == "YouTube URL":

        source_url = st.text_input(
            "YouTube video URL",
            placeholder="https://www.youtube.com/watch?v=...",
        )

    else:

        uploaded_file = st.file_uploader(
            "Upload meeting recording",
            type=["mp3", "wav", "m4a", "mp4", "webm", "ogg"],
        )

    col1, col2 = st.columns(2)

    with col1:

        language = st.selectbox(
            "Transcription language",
            ["english", "hinglish"],
        )

    with col2:

        meeting_type = st.selectbox(
            "Vector store",
            [
                "Create new meeting",
                "Load existing meeting",
            ],
        )

    process_clicked = st.button(
        "PROCESS MEETING ↗",
        use_container_width=True,
    )

    if process_clicked:

        if input_method == "YouTube URL" and not source_url.strip():

            st.error("Please provide a YouTube URL.")

        elif input_method == "Upload local file" and uploaded_file is None:

            st.error("Please upload an audio or video file.")

        else:

            temp_path = None

            progress_bar = st.progress(
                0,
                text="Initializing Plixy...",
            )

            timer_placeholder = st.empty()
            status_placeholder = st.empty()

            estimated_seconds = estimate_processing_time(
                "upload" if uploaded_file else "youtube",
                uploaded_file,
            )

            with timer_placeholder:

                render_countdown(estimated_seconds)

            def update_pipeline_ui(value, message):

                progress_bar.progress(
                    value,
                    text=message,
                )

                status_placeholder.markdown(
                    f"**CURRENT STAGE:** {message}"
                )

            try:

                if uploaded_file is not None:

                    suffix = Path(uploaded_file.name).suffix

                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=suffix,
                    ) as temp_file:

                        temp_file.write(uploaded_file.getvalue())
                        temp_path = temp_file.name

                    source = temp_path

                else:

                    source = source_url.strip()

                is_new = meeting_type == "Create new meeting"

                result = run_pipeline(
                    source=source,
                    language=language,
                    is_new_meeting=is_new,
                    progress_callback=update_pipeline_ui,
                )

                st.session_state.meeting = {
                    key: value
                    for key, value in result.items()
                    if key != "rag_chain"
                }

                st.session_state.rag_chain = result["rag_chain"]
                st.session_state.chat_history = []

                timer_placeholder.empty()

                progress_bar.progress(
                    1.0,
                    text="Meeting processing complete!",
                )

                status_placeholder.success(
                    "Your meeting has been processed successfully!"
                )

            except Exception as error:

                timer_placeholder.empty()
                status_placeholder.empty()

                st.error(
                    f"Processing failed: {error}"
                )

            finally:

                if temp_path and os.path.exists(temp_path):

                    os.remove(temp_path)


# ==================================================
# SECTION 02 - MEETING RESULTS
# ==================================================

if st.session_state.meeting:

    meeting = st.session_state.meeting

    st.markdown("---")

    render_html(
        """
        <div class="eyebrow">
            02 / INTELLIGENCE REPORT
        </div>

        <div class="section-heading">
            Your meeting, decoded.
        </div>
        """
    )

    safe_title = html.escape(str(meeting["title"]))

    render_html(
        f"""
        <div class="orange-card">

            <div style="
                font-family:'Space Mono',monospace;
                font-size:0.75rem;
                font-weight:700;
                letter-spacing:1px;
            ">
                MEETING TITLE
            </div>

            <div style="
                font-size:clamp(1.5rem,4vw,2.4rem);
                font-weight:700;
                margin-top:8px;
            ">
                {safe_title}
            </div>

        </div>
        """
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Summary",
            "Action Items",
            "Decisions",
            "Questions",
            "Transcript",
        ]
    )

    with tab1:

        st.markdown("### Meeting Summary")
        st.markdown(str(meeting["summary"]))

    with tab2:

        st.markdown("### Action Items")
        st.markdown(str(meeting["action_items"]))

    with tab3:

        st.markdown("### Key Decisions")
        st.markdown(str(meeting["key_decisions"]))

    with tab4:

        st.markdown("### Open Questions")
        st.markdown(str(meeting["open_questions"]))

    with tab5:

        st.markdown("### Full Transcript")

        st.text_area(
            "Transcript",
            value=meeting["transcript"],
            height=400,
            disabled=True,
            label_visibility="collapsed",
        )

        st.download_button(
            "DOWNLOAD TRANSCRIPT ↗",
            data=meeting["transcript"],
            file_name="plixy_transcript.txt",
            mime="text/plain",
            use_container_width=True,
        )


# ==================================================
# SECTION 03 - MEETING COPILOT
# ==================================================

if st.session_state.rag_chain is not None:

    st.markdown("---")

    render_html(
        """
        <div class="eyebrow">
            03 / RAG ASSISTANT
        </div>

        <div class="section-heading">
            Talk to your meeting.
        </div>

        <div class="section-caption">
            Ask questions and retrieve information from your transcript.
        </div>
        """
    )

    with st.container(border=True):

        for message in st.session_state.chat_history:

            with st.chat_message(message["role"]):

                st.markdown(message["content"])

        prompt = st.chat_input(
            "Ask anything about your meeting..."
        )

        if prompt:

            st.session_state.chat_history.append(
                {
                    "role": "user",
                    "content": prompt,
                }
            )

            with st.chat_message("user"):

                st.markdown(prompt)

            with st.chat_message("assistant"):

                with st.spinner("Searching your meeting..."):

                    try:

                        answer = ask_question(
                            st.session_state.rag_chain,
                            prompt,
                        )

                        answer = str(answer)

                        st.markdown(answer)

                        st.session_state.chat_history.append(
                            {
                                "role": "assistant",
                                "content": answer,
                            }
                        )

                    except Exception as error:

                        st.error(
                            f"Unable to generate answer: {error}"
                        )


# ==================================================
# SECTION 04 - PLAYLIST CALCULATOR
# ==================================================

st.markdown("---")

render_html(
    """
    <div class="eyebrow">
        04 / WATCH TIME ANALYTICS
    </div>

    <div class="section-heading">
        Playlist time calculator.
    </div>

    <div class="section-caption">
        Calculate how long your YouTube playlist will take to finish.
        No video downloads required.
    </div>
    """
)

with st.container(border=True):

    st.markdown("#### KNOW YOUR WATCH TIME.")

    with st.form("playlist_form"):

        playlist_url = st.text_input(
            "YouTube playlist URL",
            placeholder="Paste your playlist URL here...",
        )

        start_video = st.number_input(
            "Start from video number",
            min_value=1,
            value=1,
            step=1,
            help=(
                "For example, entering 15 calculates "
                "video 15 through the final video."
            ),
        )

        calculate_clicked = st.form_submit_button(
            "CALCULATE WATCH TIME ↗",
            use_container_width=True,
        )

    if calculate_clicked:

        if not playlist_url.strip():

            st.error("Please enter a playlist URL.")

        elif "list=" not in playlist_url:

            st.error(
                "This doesn't look like a YouTube playlist URL."
            )

        else:

            try:

                with st.spinner("Fetching playlist metadata..."):

                    playlist_result = calculate_playlist_duration(
                        playlist_url,
                        start_video=int(start_video),
                    )

                st.session_state.playlist_result = playlist_result

                st.success("Playlist analysis complete!")

            except Exception as error:

                st.error(
                    f"Playlist calculation failed: {error}"
                )


# ==================================================
# PLAYLIST RESULTS
# ==================================================

if st.session_state.playlist_result:

    result = st.session_state.playlist_result

    st.markdown("### PLAYLIST ANALYSIS")

    if result["total_seconds"] > 0:

        render_html(
            f"""
            <div class="orange-card">

                <div style="
                    font-family:'Space Mono',monospace;
                    font-size:0.75rem;
                    font-weight:700;
                ">
                    TOTAL WATCH TIME / 1X
                </div>

                <div style="
                    font-size:clamp(2rem,6vw,3.5rem);
                    font-weight:700;
                    letter-spacing:-2px;
                ">
                    {format_duration(result["total_seconds"])}
                </div>

                <div style="font-size:0.85rem;font-weight:600;">
                    {result["processed_videos"]} videos included
                    · Starting video #{result["start_video"]}
                </div>

            </div>
            """
        )

        speeds = [1, 1.25, 1.5, 1.75, 2]

        speed_columns = st.columns(2)

        for index, speed in enumerate(speeds):

            duration = result["total_seconds"] / speed

            with speed_columns[index % 2]:

                render_html(
                    f"""
                    <div class="brutal-card">

                        <div class="stat-label">
                            PLAYBACK SPEED
                        </div>

                        <div class="stat-value">
                            {speed}x
                        </div>

                        <div style="
                            color:#FF5A1F;
                            font-weight:700;
                            font-size:1.15rem;
                            margin-top:8px;
                        ">
                            {format_duration(duration)}
                        </div>

                    </div>
                    """
                )

        st.markdown("#### PLAYLIST DETAILS")

        st.write(
            f"**Playlist videos:** {result['total_videos']}"
        )

        st.write(
            f"**Processed videos:** {result['processed_videos']}"
        )

        st.write(
            f"**Skipped videos:** {result['skipped_videos']}"
        )

        if result["skipped_entries"]:

            with st.expander("View unavailable / skipped videos"):

                for item in result["skipped_entries"]:

                    st.write(
                        f"Video #{item['number']}: {item['title']}"
                    )

    else:

        st.warning(
            "No playable video durations were found."
        )


# ==================================================
# FOOTER
# ==================================================

st.markdown("---")

render_html(
    """
    <div class="footer">

        <div class="footer-brand">
            Plixy<span style="color:#FF5A1F;">.</span>
        </div>

        <div class="footer-credit">
            MADE BY AYMAAN SHABBIR
        </div>

        <div class="footer-powered">
            POWERED BY MISTRAL AI / 2026
        </div>

    </div>
    """
)
