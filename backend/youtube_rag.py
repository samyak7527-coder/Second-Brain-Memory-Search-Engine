import os
import re
import streamlit as st
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_classic.chains import RetrievalQA
# from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

# --- Load ENV ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Config ---
CHROMA_DIR = "chroma_store"
EMBED_MODEL = "intfloat/e5-large-v2"

# --- Extract video ID from URL ---
def extract_video_id(url):
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

# --- Fetch transcript (fixed for youtube-transcript-api v1.x) ---
def fetch_transcript(video_id):
    try:
        ytt_api = YouTubeTranscriptApi()  # Must instantiate in v1.x
        transcript_list = ytt_api.list(video_id)  # .list() replaces .list_transcripts()

        # 1. Try manual English transcript
        try:
            transcript = transcript_list.find_manually_created_transcript(['en'])
        except NoTranscriptFound:
            # 2. Fallback to auto-generated English
            transcript = transcript_list.find_generated_transcript(['en'])

        data = transcript.fetch()
        # v1.x returns objects with .text attribute, not dicts
        return " ".join([t.text for t in data])

    except TranscriptsDisabled:
        print("Transcripts are disabled for this video.")
        return None
    except Exception as e:
        print("Transcript error:", e)
        return None

# --- Streamlit UI ---
st.set_page_config(page_title="YouTube AI Assistant", layout="wide")
st.title("🎥 YouTube Transcript AI Assistant")

video_url = st.text_input("Enter YouTube Video URL")

if st.button("Process Video"):

    video_id = extract_video_id(video_url)

    if not video_id:
        st.error("Invalid YouTube URL")
        st.stop()

    st.info("Fetching transcript...")
    transcript = fetch_transcript(video_id)

    if not transcript:
        st.error("Transcript not available for this video.")
        st.stop()

    st.success("Transcript fetched!")

    # --- Split ---
    docs = [Document(page_content=transcript)]
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    # --- Embeddings ---
    embedding = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        encode_kwargs={"normalize_embeddings": True}
    )

    vector_store = Chroma.from_documents(chunks, embedding)

    # --- LLM ---
    llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name="openai/gpt-oss-120b",
        temperature=0.2
    )

    # --- Summary Prompt ---
    summary_prompt = PromptTemplate(
        input_variables=["text"],
        template="""
        Summarize the following YouTube transcript clearly:

        {text}

        Summary:
        """
    )

    st.info("Generating summary...")
    summary = llm.invoke(summary_prompt.format(text=transcript[:5000]))

    st.subheader("📌 Video Summary")
    st.write(summary.content)

    # --- QA Prompt ---
    qa_prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""
        Answer using ONLY the context below.

        Context:
        {context}

        Question:
        {question}

        If the answer is not in the context, say: "Not found in transcript."
        """
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
        chain_type_kwargs={"prompt": qa_prompt}
    )

    # Store chain and vector store in session state so they survive reruns
    st.session_state.qa_chain = qa_chain
    st.session_state.processed = True

# --- Chat (only shown after processing) ---
if st.session_state.get("processed"):

    st.subheader("💬 Ask Questions")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_query = st.text_input("Ask something about the video", key="user_query")

    if st.button("Ask") and user_query:
        response = st.session_state.qa_chain.invoke({"query": user_query})

        st.session_state.chat_history.append(("You", user_query))
        st.session_state.chat_history.append(("AI", response["result"]))

    # --- Display chat ---
    for role, msg in st.session_state.chat_history:
        if role == "You":
            st.markdown(f"**🧑 {msg}**")
        else:
            st.markdown(f"**🤖 {msg}**")