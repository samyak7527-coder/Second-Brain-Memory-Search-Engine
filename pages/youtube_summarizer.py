import streamlit as st
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.youtube_rag import (
    fetch_youtube_transcript,
    create_qa_chain,
    query_youtube_content
)

# Page config
st.set_page_config(
    page_title="YouTube Summarizer",
    page_icon="🎥",
    layout="wide"
)

st.title("🎥 YouTube Video Summarizer & Q&A")
st.markdown("Extract insights from YouTube videos using AI-powered summarization and Q&A")

# Initialize session state
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None
if "transcript_text" not in st.session_state:
    st.session_state.transcript_text = None
if "video_id" not in st.session_state:
    st.session_state.video_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chunk_count" not in st.session_state:
    st.session_state.chunk_count = 0

# Sidebar for video upload
with st.sidebar:
    st.header("📹 Video Input")
    st.divider()
    
    video_input = st.text_input(
        "Enter YouTube Video URL or Video ID:",
        placeholder="https://www.youtube.com/watch?v=... or dQw4w9WgXcQ",
        help="Paste a YouTube video URL or just the video ID"
    )
    
    if st.button("🔗 Fetch Transcript", use_container_width=True, type="primary"):
        if video_input.strip():
            with st.spinner("Fetching transcript from YouTube..."):
                transcript_text, video_id = fetch_youtube_transcript(video_input.strip())
                
                if transcript_text:
                    st.session_state.transcript_text = transcript_text
                    st.session_state.video_id = video_id
                    st.session_state.messages = []  # Clear previous messages
                    
                    # Create QA chain
                    with st.spinner("Creating AI model... This may take a moment"):
                        try:
                            qa_chain, chunk_count = create_qa_chain(transcript_text, video_id)
                            st.session_state.qa_chain = qa_chain
                            st.session_state.chunk_count = chunk_count
                            st.success(f"✅ Video processed successfully!\n\n📊 Chunks created: {chunk_count}")
                        except Exception as e:
                            st.error(f"❌ Error creating AI model: {str(e)}")
                else:
                    st.error(f"❌ {video_id}")
        else:
            st.warning("Please enter a YouTube URL or video ID")
    
    st.divider()
    
    if st.session_state.qa_chain:
        st.info(f"✅ Video loaded: {st.session_state.video_id}\n📊 Chunks: {st.session_state.chunk_count}")
        
        if st.button("🔄 Clear & Load New Video", use_container_width=True):
            st.session_state.qa_chain = None
            st.session_state.transcript_text = None
            st.session_state.video_id = None
            st.session_state.messages = []
            st.session_state.chunk_count = 0
            st.rerun()

# Main content
if st.session_state.qa_chain:
    # Create two columns
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📄 Transcript Preview")
        with st.expander("View Full Transcript", expanded=False):
            st.text_area(
                "Full Transcript:",
                value=st.session_state.transcript_text[:2000] + "..." if len(st.session_state.transcript_text) > 2000 else st.session_state.transcript_text,
                height=300,
                disabled=True
            )
    
    with col2:
        st.subheader("💬 Ask Questions")
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask anything about this video..."):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("🤔 Analyzing video..."):
                    response = query_youtube_content(st.session_state.qa_chain, prompt)
                    answer = response.get("result", "Could not generate an answer")
                    
                    st.markdown(answer)
                    
                    # Add to history
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    
                    # Show source documents
                    with st.expander("📌 Source Information"):
                        if response.get("source_documents"):
                            for i, doc in enumerate(response["source_documents"], 1):
                                st.markdown(f"**Source {i}:**")
                                st.markdown(f"*{doc.page_content[:200]}...*")
                                st.divider()
                        else:
                            st.info("No source documents found")

else:
    # Welcome state
    st.info(
        """
        👋 **Welcome to YouTube Video Summarizer!**
        
        This tool uses AI to help you:
        - 📝 Extract transcripts from YouTube videos
        - 🤖 Ask questions about video content
        - 📊 Get relevant excerpts and timestamps
        - 🧠 Understand key concepts from videos
        
        **Getting Started:**
        1. Enter a YouTube URL or video ID in the sidebar
        2. Click "Fetch Transcript" to load the video
        3. Ask questions about the video content
        4. Get AI-powered answers with source references
        
        **Supported Input Formats:**
        - Full URL: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
        - Short URL: `https://youtu.be/dQw4w9WgXcQ`
        - Video ID: `dQw4w9WgXcQ`
        """
    )

# Footer
st.divider()
st.markdown(
    """
    ---
    **YouTube Summarizer** - AI-powered video analysis
    
    Built with 🔧 Streamlit, LangChain, Groq LLM, and HuggingFace Embeddings
    """
)
