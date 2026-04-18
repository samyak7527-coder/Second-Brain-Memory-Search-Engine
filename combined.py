import os
import re
import sys
import io
import json
import datetime
import streamlit as st
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.ingest import ingest_text
from backend.rag import generate_answer

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

from pypdf import PdfReader
from pptx import Presentation

# ─────────────────────────────────────────────
# ENV & Constants
# ─────────────────────────────────────────────

load_dotenv()
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
EMBED_MODEL    = "intfloat/e5-large-v2"
DIGEST_STORE   = "digest_history.json"   # flat-file persistence for past digests


# ─────────────────────────────────────────────
# File Extraction
# ─────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for i, page in enumerate(reader.pages):
        t = page.extract_text()
        if t and t.strip():
            pages.append(f"[Page {i+1}]\n{t.strip()}")
    return "\n\n".join(pages)


def extract_text_from_pptx(file_bytes: bytes) -> str:
    prs = Presentation(io.BytesIO(file_bytes))
    slides = []
    for i, slide in enumerate(prs.slides):
        parts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    line = " ".join(r.text for r in para.runs).strip()
                    if line:
                        parts.append(line)
        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                parts.append(f"[Notes]: {notes}")
        if parts:
            slides.append(f"[Slide {i+1}]\n" + "\n".join(parts))
    return "\n\n".join(slides)


# ─────────────────────────────────────────────
# LLM helpers
# ─────────────────────────────────────────────

def get_llm() -> ChatGroq:
    return ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name="openai/gpt-oss-120b",
        temperature=0.2
    )


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        encode_kwargs={"normalize_embeddings": True}
    )


def summarise_with_llm(llm: ChatGroq, text: str, doc_type: str = "document") -> str:
    prompt = PromptTemplate(
        input_variables=["doc_type", "text"],
        template="""You are a helpful assistant. Summarise the following {doc_type} clearly and concisely.
Include all key points, main topics, and any important details.

{doc_type} content:
{text}

Summary:"""
    )
    truncated = text[:6000] + ("\n\n[... content truncated ...]" if len(text) > 6000 else "")
    return llm.invoke(prompt.format(doc_type=doc_type, text=truncated)).content


# ─────────────────────────────────────────────
# Knowledge Digest Engine
# ─────────────────────────────────────────────

# Broad semantic probe queries used to pull representative chunks
# from ChromaDB via similarity search, covering a wide knowledge surface.
PROBE_QUERIES = [
    "main concepts and key ideas",
    "important facts and insights",
    "definitions and explanations",
    "conclusions and takeaways",
    "processes and how things work",
    "examples and case studies",
    "people organizations and entities mentioned",
    "problems challenges and solutions",
    "data statistics and numbers",
    "recommendations and action items",
]

DIGEST_PROMPT_TEMPLATE = """You are an expert knowledge curator and analyst.

Below is a representative sample of content from a personal knowledge base, retrieved using semantic search across multiple topics.

Your task is to generate a comprehensive **{period} Knowledge Digest** in structured Markdown.

The digest MUST include these sections:

## 📌 Executive Summary
2–3 sentences capturing the overall themes and scope of what was stored this {period}.

## 🧠 Key Concepts & Ideas
A bullet list of the most important concepts, ideas, and insights discovered. Group related ideas together. Be specific — avoid vague generalities.

## 🔗 Relationships & Connections
Identify non-obvious connections, patterns, or recurring themes across different pieces of content. What ideas appear in multiple sources? What contradicts or complements each other?

## 💡 Notable Insights
3–5 standout insights or facts worth remembering — things that are surprising, counter-intuitive, or highly actionable.

## 📚 Topics Covered
A categorised list of domains/subjects present in the knowledge base (e.g., Technology, Science, Business, History, etc.).

## ❓ Questions to Explore
Based on what was ingested, list 3–5 open questions or knowledge gaps worth investigating further.

## 🎯 Action Items & Recommendations
Specific, concrete next steps suggested by the content (if any).

---

Retrieved knowledge base content ({chunk_count} chunks sampled):

{context}

---

Generate the {period} Knowledge Digest now. Be thorough, insightful, and specific. Reference actual content from the knowledge base — do not hallucinate or add external information.
"""


def fetch_semantic_sample(chroma_dir: str, k_per_query: int = 8) -> tuple[list[str], int]:
    """
    Run multiple probe queries against ChromaDB to get a broad,
    semantically diverse sample of stored chunks. Returns
    (list_of_chunk_texts, total_unique_chunks_found).
    """
    try:
        embeddings = get_embeddings()
        vector_store = Chroma(
            persist_directory=chroma_dir,
            embedding_function=embeddings
        )

        seen_ids: set = set()
        chunks: list[str] = []

        for query in PROBE_QUERIES:
            results = vector_store.similarity_search_with_score(query, k=k_per_query)
            for doc, score in results:
                # Use content hash as dedup key since Chroma doesn't expose stable IDs easily
                content_key = hash(doc.page_content[:200])
                if content_key not in seen_ids:
                    seen_ids.add(content_key)
                    chunks.append(doc.page_content)

        return chunks, len(chunks)

    except Exception as e:
        raise RuntimeError(f"Could not read from ChromaDB: {e}")


def generate_knowledge_digest(period: str, chroma_dir: str) -> dict:
    """
    Core digest generation function.
    Returns a dict with keys: period, generated_at, chunk_count, content.
    """
    llm = get_llm()

    # 1. Retrieve a semantic sample from the vector store
    chunks, chunk_count = fetch_semantic_sample(chroma_dir, k_per_query=8)

    if chunk_count == 0:
        raise ValueError("No content found in the knowledge base. Ingest some documents first.")

    # 2. Build context — cap at ~12 000 chars to stay within context window
    context_parts = []
    total_chars = 0
    char_limit = 12000
    for i, chunk in enumerate(chunks):
        entry = f"--- Chunk {i+1} ---\n{chunk}"
        if total_chars + len(entry) > char_limit:
            break
        context_parts.append(entry)
        total_chars += len(entry)

    context_text = "\n\n".join(context_parts)
    actual_chunks_used = len(context_parts)

    # 3. Call LLM
    prompt = DIGEST_PROMPT_TEMPLATE.format(
        period=period,
        chunk_count=actual_chunks_used,
        context=context_text
    )
    digest_content = llm.invoke(prompt).content

    return {
        "period": period,
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "chunk_count": actual_chunks_used,
        "content": digest_content,
    }


# ─────────────────────────────────────────────
# Digest Persistence (flat JSON file)
# ─────────────────────────────────────────────

def load_digest_history() -> list[dict]:
    if os.path.exists(DIGEST_STORE):
        try:
            with open(DIGEST_STORE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_digest(digest: dict) -> None:
    history = load_digest_history()
    history.insert(0, digest)   # newest first
    history = history[:20]       # keep last 20
    with open(DIGEST_STORE, "w") as f:
        json.dump(history, f, indent=2)


# ─────────────────────────────────────────────
# YouTube Helpers
# ─────────────────────────────────────────────

def extract_video_id(url: str):
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None


def fetch_transcript(video_id: str):
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        try:
            transcript = transcript_list.find_manually_created_transcript(['en'])
        except NoTranscriptFound:
            transcript = transcript_list.find_generated_transcript(['en'])
        data = transcript.fetch()
        return " ".join([t.text for t in data])
    except TranscriptsDisabled:
        return None
    except Exception as e:
        print("Transcript error:", e)
        return None


def build_youtube_qa_chain(transcript_text: str):
    docs = [Document(page_content=transcript_text)]
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    vector_store = Chroma.from_documents(chunks, get_embeddings())
    llm = get_llm()
    qa_prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""Answer using ONLY the context below.

Context:
{context}

Question:
{question}

If the answer is not in the context, say: "Not found in transcript."
"""
    )
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
        chain_type_kwargs={"prompt": qa_prompt}
    )
    return chain, llm


# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Second Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# Session State Init
# ─────────────────────────────────────────────

defaults = {
    "messages":          [],
    "ingested_chunks":   0,
    "active_tab":        "docs",       # "docs" | "youtube" | "digest"
    "yt_processed":      False,
    "yt_summary":        "",
    "yt_chat_history":   [],
    "yt_qa_chain":       None,
    "file_summary":      "",
    "file_name":         "",
    "file_ingested":     False,
    # Digest
    "digest_result":     None,         # latest generated digest dict
    "digest_history":    [],           # loaded from disk
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Load digest history from disk once per session
if not st.session_state.digest_history:
    st.session_state.digest_history = load_digest_history()


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────

with st.sidebar:
    st.title("🧠 Second Brain")
    st.markdown("Your personal knowledge assistant")
    st.divider()

    st.subheader("🔀 Navigate")
    mode = st.radio(
        "Navigate:",
        ["📄 Document RAG", "🎥 YouTube RAG", "📅 Knowledge Digest"],
        index={"docs": 0, "youtube": 1, "digest": 2}.get(st.session_state.active_tab, 0),
        label_visibility="collapsed"
    )
    if "Document" in mode:
        st.session_state.active_tab = "docs"
    elif "YouTube" in mode:
        st.session_state.active_tab = "youtube"
    else:
        st.session_state.active_tab = "digest"

    st.divider()

    # ── Document Mode Sidebar ──
    if st.session_state.active_tab == "docs":
        st.subheader("📚 Document Management")

        doc_input_mode = st.radio(
            "Input method:",
            ["✏️ Paste Text", "📎 Upload File"],
            horizontal=True,
            label_visibility="collapsed"
        )

        if "Paste" in doc_input_mode:
            input_text = st.text_area(
                "Paste text or document content:",
                height=160,
                placeholder="Articles, notes — any text you want to learn from..."
            )
            if st.button("📤 Ingest Text", use_container_width=True, type="primary"):
                if input_text.strip():
                    with st.spinner("Processing and storing..."):
                        try:
                            result = ingest_text(input_text)
                            st.session_state.ingested_chunks += result.get("chunks", 0)
                            st.success(f"✅ {result['chunks']} chunks stored.")
                        except Exception as e:
                            st.error(f"❌ {e}")
                else:
                    st.warning("Please enter some text first.")
        else:
            st.markdown("**Supported:** PDF (`.pdf`) · PowerPoint (`.pptx`)")
            uploaded_file = st.file_uploader(
                "Choose a file:",
                type=["pdf", "pptx"],
                label_visibility="collapsed"
            )
            if uploaded_file is not None:
                fext      = uploaded_file.name.rsplit(".", 1)[-1].lower()
                doc_type  = "PDF document" if fext == "pdf" else "PowerPoint presentation"
                icon      = "📄" if fext == "pdf" else "📊"
                st.markdown(f"{icon} **{uploaded_file.name}**")
                file_bytes = uploaded_file.read()
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🤖 Summarise", use_container_width=True, type="primary"):
                        with st.spinner("Extracting & summarising..."):
                            try:
                                raw_text = (extract_text_from_pdf(file_bytes) if fext == "pdf"
                                            else extract_text_from_pptx(file_bytes))
                                if not raw_text.strip():
                                    st.error("No readable text found.")
                                else:
                                    summary = summarise_with_llm(get_llm(), raw_text, doc_type)
                                    st.session_state.file_summary  = summary
                                    st.session_state.file_name     = uploaded_file.name
                                    st.session_state.file_ingested = False
                                    st.success("✅ Summary ready!")
                            except Exception as e:
                                st.error(f"❌ {e}")
                with col2:
                    if st.button("📥 Ingest", use_container_width=True):
                        with st.spinner("Ingesting..."):
                            try:
                                raw_text = (extract_text_from_pdf(file_bytes) if fext == "pdf"
                                            else extract_text_from_pptx(file_bytes))
                                if not raw_text.strip():
                                    st.error("No readable text found.")
                                else:
                                    result = ingest_text(raw_text)
                                    st.session_state.ingested_chunks += result.get("chunks", 0)
                                    st.session_state.file_ingested = True
                                    st.success(f"✅ {result['chunks']} chunks ingested!")
                            except Exception as e:
                                st.error(f"❌ {e}")

        st.divider()
        st.info(f"📊 Total chunks stored: {st.session_state.ingested_chunks}")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # ── YouTube Mode Sidebar ──
    elif st.session_state.active_tab == "youtube":
        st.subheader("🎥 YouTube Video")
        video_url = st.text_input("YouTube URL:",
                                  placeholder="https://www.youtube.com/watch?v=...")
        if st.button("⚙️ Process Video", use_container_width=True, type="primary"):
            if not video_url.strip():
                st.warning("Please enter a URL.")
            else:
                video_id = extract_video_id(video_url)
                if not video_id:
                    st.error("Invalid YouTube URL.")
                else:
                    with st.spinner("Fetching transcript..."):
                        transcript = fetch_transcript(video_id)
                    if not transcript:
                        st.error("No English transcript available.")
                    else:
                        with st.spinner("Building index & summarising..."):
                            qa_chain, llm = build_youtube_qa_chain(transcript)
                            yt_prompt = PromptTemplate(
                                input_variables=["text"],
                                template="Summarise the following YouTube transcript clearly:\n\n{text}\n\nSummary:"
                            )
                            summary = llm.invoke(yt_prompt.format(text=transcript[:5000]))
                        st.session_state.yt_qa_chain     = qa_chain
                        st.session_state.yt_summary      = summary.content
                        st.session_state.yt_processed    = True
                        st.session_state.yt_chat_history = []
                        st.success("✅ Video processed!")
        if st.session_state.yt_processed:
            st.divider()
            if st.button("🗑️ Clear YouTube Chat", use_container_width=True):
                st.session_state.yt_chat_history = []
                st.rerun()

    # ── Digest Mode Sidebar ──
    else:
        st.subheader("📅 Digest Settings")
        st.markdown("Generate a structured synthesis of everything in your knowledge base.")
        st.divider()

        digest_period = st.selectbox(
            "Digest period:",
            ["Weekly", "Monthly", "Custom Range"],
            index=0
        )

        chroma_dir = st.text_input(
            "ChromaDB directory:",
            value="chroma_store",
            help="Path to your ChromaDB persist directory (set during ingest)."
        )

        st.markdown(f"**Knowledge base:** `{chroma_dir}`")
        st.info(f"📊 Chunks ingested this session: {st.session_state.ingested_chunks}")

        st.divider()

        if st.button(
            f"⚡ Generate {digest_period} Digest",
            use_container_width=True,
            type="primary"
        ):
            with st.spinner(f"Running semantic search across your knowledge base..."):
                try:
                    digest = generate_knowledge_digest(digest_period, chroma_dir)
                    st.session_state.digest_result = digest
                    save_digest(digest)
                    st.session_state.digest_history = load_digest_history()
                    st.success("✅ Digest generated!")
                except ValueError as e:
                    st.error(f"⚠️ {e}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        st.divider()
        st.caption(f"💾 {len(st.session_state.digest_history)} past digest(s) saved")


# ─────────────────────────────────────────────
# Main Content
# ─────────────────────────────────────────────

# ════════════════════════════════════════════
# TAB: Document RAG
# ════════════════════════════════════════════
if st.session_state.active_tab == "docs":

    st.title("📄 Document Q&A")
    st.markdown("Ingest documents from the sidebar, then ask questions below.")

    if st.session_state.file_summary:
        st.divider()
        fext_d = st.session_state.file_name.rsplit(".", 1)[-1].upper() if st.session_state.file_name else ""
        icon   = "📄" if fext_d == "PDF" else "📊"
        with st.expander(f"{icon} AI Summary — {st.session_state.file_name}", expanded=True):
            st.markdown(st.session_state.file_summary)
            if not st.session_state.file_ingested:
                st.warning("⚠️ Not ingested yet — click **Ingest** in the sidebar to enable Q&A over this file.")
            else:
                st.success("✅ Ingested and ready for Q&A.")
        if st.button("✖ Dismiss Summary"):
            st.session_state.file_summary  = ""
            st.session_state.file_name     = ""
            st.session_state.file_ingested = False
            st.rerun()

    st.divider()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask anything about your documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    response = generate_answer(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    err = f"❌ Error: {e}"
                    st.error(err)
                    st.session_state.messages.append({"role": "assistant", "content": err})


# ════════════════════════════════════════════
# TAB: YouTube RAG
# ════════════════════════════════════════════
elif st.session_state.active_tab == "youtube":

    st.title("🎥 YouTube Q&A")
    st.markdown("Enter a YouTube URL in the sidebar and click **Process Video** to begin.")
    st.divider()

    if not st.session_state.yt_processed:
        st.info("👈 Paste a YouTube URL in the sidebar and hit **Process Video**.")
    else:
        with st.expander("📌 Video Summary", expanded=True):
            st.markdown(st.session_state.yt_summary)
        st.divider()
        st.subheader("💬 Ask about the video")

        for role, msg in st.session_state.yt_chat_history:
            with st.chat_message("user" if role == "You" else "assistant"):
                st.markdown(msg)

        if yt_query := st.chat_input("Ask something about the video..."):
            st.session_state.yt_chat_history.append(("You", yt_query))
            with st.chat_message("user"):
                st.markdown(yt_query)
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    try:
                        result = st.session_state.yt_qa_chain.invoke({"query": yt_query})
                        answer = result["result"]
                        st.markdown(answer)
                        st.session_state.yt_chat_history.append(("AI", answer))
                    except Exception as e:
                        err = f"❌ Error: {e}"
                        st.error(err)
                        st.session_state.yt_chat_history.append(("AI", err))


# ════════════════════════════════════════════
# TAB: Knowledge Digest
# ════════════════════════════════════════════
else:

    st.title("📅 Knowledge Digest")
    st.markdown(
        "Automatically synthesise everything in your knowledge base into a structured report — "
        "key concepts, relationships, insights, and action items."
    )

    # ── How it works banner ──
    with st.expander("ℹ️ How this works", expanded=False):
        st.markdown("""
**The digest engine works in three steps:**

1. **Semantic Sampling** — runs 10 broad probe queries (e.g. *"key concepts and ideas"*, *"processes and how things work"*, *"data and statistics"*) against your ChromaDB vector store using similarity search, pulling up to ~80 unique chunks that represent the full breadth of your knowledge base.

2. **Context Assembly** — deduplicates and assembles the chunks into a rich context window (capped at ~12 000 chars to stay within the LLM's context limit).

3. **LLM Synthesis** — sends the assembled context to the Groq LLM with a structured prompt that asks it to identify key concepts, cross-document relationships, notable insights, open questions, and action items.

The result is a living snapshot of your Second Brain.
        """)

    st.divider()

    # ── Latest Digest Result ──
    if st.session_state.digest_result:
        d = st.session_state.digest_result

        # Metadata bar
        meta_col1, meta_col2, meta_col3 = st.columns(3)
        with meta_col1:
            st.metric("📆 Period", d["period"])
        with meta_col2:
            st.metric("🕐 Generated", d["generated_at"])
        with meta_col3:
            st.metric("📦 Chunks Analysed", d["chunk_count"])

        st.divider()

        # Digest content (rendered as Markdown)
        st.markdown(d["content"])

        st.divider()

        # Download button
        st.download_button(
            label="⬇️ Download Digest (.md)",
            data=d["content"],
            file_name=f"digest_{d['period'].lower()}_{d['generated_at'].replace(' ', '_').replace(':', '-')}.md",
            mime="text/markdown",
            use_container_width=True
        )

    else:
        # Empty state
        st.info(
            "👈 Select a period and click **Generate Digest** in the sidebar.\n\n"
            "Make sure you have ingested at least a few documents first."
        )

    # ── Past Digests ──
    if st.session_state.digest_history:
        st.divider()
        st.subheader("🗂️ Past Digests")
        st.caption("The last 20 generated digests are saved locally.")

        for i, past in enumerate(st.session_state.digest_history):
            label = f"**{past['period']} Digest** — {past['generated_at']}  ·  {past['chunk_count']} chunks"
            with st.expander(label, expanded=False):
                st.markdown(past["content"])
                st.download_button(
                    label="⬇️ Download",
                    data=past["content"],
                    file_name=f"digest_{past['period'].lower()}_{past['generated_at'].replace(' ', '_').replace(':', '-')}.md",
                    mime="text/markdown",
                    key=f"dl_past_{i}"
                )


# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────

st.divider()
st.markdown(
    "<p style='text-align:center; color:gray; font-size:13px;'>"
    "🧠 <b>Second Brain</b> — Streamlit · ChromaDB · LangChain · Groq · pypdf · python-pptx"
    "</p>",
    unsafe_allow_html=True
)