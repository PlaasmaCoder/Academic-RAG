import logging
from pathlib import Path

import streamlit as st

from src.pdf_loader import MAX_PDF_SIZE_BYTES, load_pdf
from src.text_splitter import split_pages
from src.embeddings import embed_texts
from src.vector_store import collection, list_documents, save_chunks, search_chunks
from src.rag_chain import answer_question
from src.errors import AcademicRAGError, DocumentProcessingError


logger = logging.getLogger(__name__)


st.set_page_config(
    page_title="StudyDesk | Academic AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_main_menu" not in st.session_state:
    st.session_state.show_main_menu = True
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "ingest_notice" not in st.session_state:
    st.session_state.ingest_notice = None
if "light_mode" not in st.session_state:
    st.session_state.light_mode = False

if st.session_state.light_mode:
    palette = {
        "page": "#F3F5FB",
        "sidebar": "#FAFBFF",
        "surface": "#FFFFFF",
        "surface_alt": "#EEF1F8",
        "text": "#20243A",
        "muted": "#68708A",
        "border": "rgba(77, 88, 125, 0.16)",
        "hero": "linear-gradient(118deg, #E9E6FF 0%, #EFF1FF 56%, #E4F7F4 100%)",
        "hero_title": "#20243A",
        "hero_copy": "#535C76",
        "hero_kicker": "#644AE0",
        "bubble": "rgba(255, 255, 255, 0.88)",
        "shadow": "0 18px 48px rgba(41, 49, 84, 0.10)",
        "scheme": "light",
    }
else:
    palette = {
        "page": "#0D111B",
        "sidebar": "#111724",
        "surface": "#171E2D",
        "surface_alt": "#20283A",
        "text": "#F1F3FA",
        "muted": "#A4ADC2",
        "border": "rgba(164, 173, 194, 0.16)",
        "hero": "linear-gradient(118deg, #211D3C 0%, #191E31 58%, #15272E 100%)",
        "hero_title": "#F7F5FF",
        "hero_copy": "#C7CCDA",
        "hero_kicker": "#B9ADFF",
        "bubble": "rgba(23, 29, 43, 0.72)",
        "shadow": "0 18px 55px rgba(0, 0, 0, 0.22)",
        "scheme": "dark",
    }

css_variables = "\n".join(
    f"--{name.replace('_', '-')}: {value};" for name, value in palette.items()
)
st.markdown(
    f"""
    <style>
    :root {{ {css_variables} color-scheme: var(--scheme); }}
    .block-container {{ max-width: 1160px; padding: 1.7rem 2rem 3rem; }}
    [data-testid="stAppViewContainer"] {{
        background: var(--page);
        color: var(--text);
        background-image: radial-gradient(ellipse at 78% 0%, rgba(112, 91, 222, 0.10), transparent 34%);
    }}
    [data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stSidebar"] {{
        background: var(--sidebar);
        color: var(--text);
        border-right: 1px solid var(--border);
    }}
    [data-testid="stMain"] {{ background: transparent; }}
    .stMarkdown, .stMarkdown p, .stMarkdown li, label,
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{ color: var(--text); }}
    [data-testid="stCaptionContainer"], .stCaption {{ color: var(--muted) !important; }}
    .brand-mark {{
        display: inline-flex; align-items: center; justify-content: center;
        width: 42px; height: 42px; margin-right: 10px; border-radius: 14px;
        background: linear-gradient(135deg, #805DFF, #44C5BE);
        font-size: 1.35rem; vertical-align: middle;
        box-shadow: 0 8px 20px rgba(115, 87, 236, 0.24);
    }}
    .hero-card {{
        position: relative; overflow: hidden; padding: 2.1rem 2.25rem;
        border: 1px solid var(--border); border-radius: 26px;
        background: var(--hero); box-shadow: var(--shadow); margin-bottom: 1.35rem;
    }}
    .hero-card::after {{
        content: ""; position: absolute; width: 230px; height: 230px; right: -80px; top: -95px;
        border-radius: 50%; background: radial-gradient(circle, rgba(132, 111, 255, 0.20), transparent 68%);
        pointer-events: none;
    }}
    .hero-kicker {{ color: var(--hero-kicker); font-size: 0.73rem; font-weight: 750;
        letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 0.65rem; }}
    .hero-title {{ color: var(--hero-title); font-size: clamp(2rem, 4vw, 3rem);
        font-weight: 760; line-height: 1.08; letter-spacing: -0.035em; margin: 0; max-width: 780px; }}
    .hero-card .hero-copy {{ color: var(--hero-copy); font-size: 1.03rem; line-height: 1.6;
        margin: 0.85rem 0 0; max-width: 700px; }}
    .section-label {{ color: var(--muted); font-size: 0.75rem; font-weight: 700;
        letter-spacing: 0.1em; text-transform: uppercase; }}
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: var(--surface); border-color: var(--border); border-radius: 19px;
    }}
    [data-testid="stMetric"] {{ background: var(--surface); border: 1px solid var(--border);
        border-radius: 15px; padding: 0.65rem 0.8rem; }}
    .stButton > button {{ border-radius: 12px; font-weight: 650;
        transition: border-color 120ms ease, transform 120ms ease; }}
    [data-testid="stBaseButton-secondary"] {{ background: var(--surface); color: var(--text);
        border: 1px solid var(--border); }}
    [data-testid="stBaseButton-primary"] {{ box-shadow: 0 8px 20px rgba(115, 87, 236, 0.20); }}
    .stButton > button:hover {{ border-color: #9B87FF; transform: translateY(-1px); }}
    [data-testid="stChatMessage"] {{ border: 1px solid var(--border); border-radius: 18px;
        padding: 0.4rem 0.85rem; margin-bottom: 0.8rem; background: var(--bubble); }}
    [data-testid="stChatInput"] {{ border-radius: 16px; }}
    [data-testid="stChatInput"] textarea, [data-baseweb="input"] > div,
    [data-baseweb="textarea"] > div {{ background: var(--surface); color: var(--text); }}
    [data-testid="stFileUploaderDropzone"] {{ background: var(--surface); border-color: var(--border); }}
    [data-testid="stExpander"] {{ background: var(--surface); border: 1px solid var(--border); border-radius: 14px; }}
    hr {{ border-color: var(--border); }}
    </style>
    """,
    unsafe_allow_html=True,
)


def library_stats():
    documents = list_documents()
    return documents, sum(document["chunks"] for document in documents)


with st.sidebar:
    st.markdown(
        '<span class="brand-mark">📚</span><span style="font-size:1.35rem;font-weight:750;vertical-align:middle">StudyDesk</span>',
        unsafe_allow_html=True,
    )
    st.caption("Your notes, organized for better learning.")
    st.toggle(
        "☀️ Light mode",
        key="light_mode",
        help="Switch between a bright and a low-glare study theme.",
    )
    st.divider()

    st.markdown("<p class='section-label'>Your library</p>", unsafe_allow_html=True)
    try:
        indexed_documents, chunk_count = library_stats()
    except AcademicRAGError as error:
        logger.warning("Could not load document-library stats: %s", error)
        indexed_documents, chunk_count = [], 0
        st.error(str(error))
    metric_docs, metric_chunks = st.columns(2)
    metric_docs.metric("PDFs", len(indexed_documents))
    metric_chunks.metric("Passages", chunk_count)
    if indexed_documents:
        with st.expander("View indexed PDFs"):
            for document in indexed_documents:
                st.caption(f"📄 {document['source']} · {document['chunks']} passages")
    else:
        st.caption("Your library is waiting for its first PDF.")

    st.divider()
    st.markdown("<p class='section-label'>Add study materials</p>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload lecture notes, textbooks, or study guides.",
        label_visibility="collapsed",
    )
    if uploaded_files:
        st.caption(f"{len(uploaded_files)} PDF{'s' if len(uploaded_files) != 1 else ''} selected")

    if st.button("✨  Add to my library", type="primary", disabled=not uploaded_files):
        upload_folder = Path("data/uploads")
        upload_folder.mkdir(parents=True, exist_ok=True)
        all_chunks = []
        file_errors = []
        seen_names = set()

        try:
            with st.spinner("Reading PDFs and preparing searchable passages..."):
                for uploaded_file in uploaded_files:
                    safe_name = Path(uploaded_file.name).name
                    if safe_name.casefold() in seen_names:
                        file_errors.append(f"{safe_name}: duplicate filename in this upload; rename one copy.")
                        continue
                    seen_names.add(safe_name.casefold())

                    if uploaded_file.size > MAX_PDF_SIZE_BYTES:
                        file_errors.append(f"{safe_name}: file exceeds the 25 MB limit.")
                        continue

                    pdf_path = upload_folder / safe_name
                    try:
                        pdf_path.write_bytes(uploaded_file.getvalue())
                        pages = load_pdf(pdf_path)
                        document_chunks = split_pages(pages)
                        if not document_chunks:
                            raise DocumentProcessingError("No usable text chunks were found.")
                        all_chunks.extend(document_chunks)
                    except AcademicRAGError as error:
                        logger.info("Skipped uploaded PDF %s: %s", safe_name, error)
                        file_errors.append(f"{safe_name}: {error}")
                    except (OSError, ValueError) as error:
                        logger.warning("Could not process uploaded PDF %s: %s", safe_name, error)
                        file_errors.append(f"{safe_name}: could not read or process this file.")

                if not all_chunks:
                    if file_errors:
                        st.session_state.ingest_notice = {"success": None, "errors": file_errors}
                        st.rerun()
                    st.warning("No readable text was found. Try a text-based PDF.")
                else:
                    vectors = embed_texts([chunk["text"] for chunk in all_chunks])
                    saved_count = save_chunks(all_chunks, vectors)
                    st.session_state.ingest_notice = {
                        "success": f"Added {len(all_chunks)} passages. Your library now has {saved_count}.",
                        "errors": file_errors,
                    }
                    st.rerun()
        except AcademicRAGError as error:
            logger.warning("Document processing failed: %s", error)
            st.error(str(error))
        except Exception:
            logger.exception("Unexpected document-processing failure")
            st.error("An unexpected error interrupted processing. Check the terminal log for details.")

    st.divider()
    if st.button("↺  Clear chat", disabled=not st.session_state.messages):
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.session_state.show_main_menu = True
        st.rerun()
    st.caption("Answers include source pages so you can check them against your notes.")


st.markdown(
    """
    <div class="hero-card">
      <div class="hero-kicker">Your personal study companion</div>
      <h1 class="hero-title">Understand your notes.<br>One question at a time.</h1>
      <p class="hero-copy">Ask about your uploaded materials and get clear answers grounded in your PDFs, with page references to guide your next read.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.ingest_notice:
    notice = st.session_state.ingest_notice
    if isinstance(notice, str):
        st.success(notice)
    else:
        if notice.get("success"):
            st.success(notice["success"])
        if notice.get("errors"):
            st.warning("Some PDFs were skipped:\n\n" + "\n".join(
                f"- {message}" for message in notice["errors"]
            ))
    st.session_state.ingest_notice = None

try:
    has_documents = collection.count() > 0
except Exception:
    logger.exception("Could not check whether the vector database contains documents")
    has_documents = False
    st.error("The local document database could not be read. Check the terminal log for details.")

if st.session_state.show_main_menu:
    if has_documents:
        st.markdown("<p class='section-label'>A few ways to get started</p>", unsafe_allow_html=True)
        prompt_col1, prompt_col2, prompt_col3 = st.columns(3)
        suggestions = [
            ("📖", "Explain a concept", "Explain a key concept from my notes."),
            ("🔎", "Find a topic", "Where do my notes discuss an important topic?"),
            ("🧩", "Compare ideas", "Compare two related ideas from my materials."),
        ]
        for column, (icon, title, question) in zip(
            (prompt_col1, prompt_col2, prompt_col3), suggestions
        ):
            with column:
                with st.container(border=True):
                    st.markdown(f"### {icon} {title}")
                    st.caption(question)
                    if st.button("Try this", key=f"suggest_{title}"):
                        st.session_state.pending_prompt = question
                        st.session_state.show_main_menu = False
                        st.rerun()
    else:
        with st.container(border=True):
            st.markdown("### Your study space starts with a PDF")
            st.write("Add a set of notes from the sidebar. StudyDesk will make the text searchable and keep page references for its answers.")
            st.caption("Supports multiple PDFs · Page-level sources · Gemini-powered answers")

if st.session_state.messages and not st.session_state.show_main_menu:
    back_col, _ = st.columns([1.7, 4.3])
    with back_col:
        if st.button(
            "←  Back to main menu",
            key="back_to_main_menu",
            help="Return to the study suggestions. Your conversation will stay in this session.",
        ):
            st.session_state.show_main_menu = True
            st.session_state.pending_prompt = None
            st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            for source in message.get("sources", []):
                if isinstance(source, dict):
                    label = f"{source['source']} · page {source['page']}"
                    with st.expander(f"📄 {label}"):
                        st.caption(source["text"])
                else:
                    st.caption(source)

if not has_documents:
    st.info("Upload and process a PDF in the sidebar to start a study chat.")

prompt = st.chat_input(
    "Ask a question about your notes...",
    disabled=not has_documents,
)
if prompt and st.session_state.show_main_menu:
    st.session_state.pending_prompt = prompt
    st.session_state.show_main_menu = False
    st.rerun()

if prompt is None and st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
elif prompt:
    st.session_state.pending_prompt = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching your notes and preparing an answer..."):
                matches = search_chunks(prompt)
                answer = answer_question(prompt, matches)

            st.markdown(answer)
            sources = [
                {
                    "source": match["source"],
                    "page": match["page"],
                    "text": match["text"],
                }
                for match in matches
            ]
            for source in sources:
                label = f"{source['source']} · page {source['page']}"
                with st.expander(f"📄 {label}"):
                    st.caption(source["text"])
        except AcademicRAGError as error:
            logger.warning("Question-answering request failed: %s", error)
            answer = str(error)
            sources = []
            st.error(answer)
        except Exception:
            logger.exception("Unexpected question-answering failure")
            answer = "An unexpected error interrupted this request. Check the terminal log for details."
            sources = []
            st.error(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })
