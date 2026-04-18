import streamlit as st
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.ingest import ingest_text
from backend.rag import generate_answer

# Page config
st.set_page_config(
    page_title="Second Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("🧠 Second Brain - RAG System")
st.markdown("A personal knowledge assistant that learns from your documents and answers questions.")

# Initialize session state
if "messages" in st.session_state:
    pass
else:
    st.session_state.messages = []
    st.session_state.ingested_chunks = 0

# Sidebar for document ingestion
with st.sidebar:
    st.header("📚 Document Management")
    st.divider()
    
    # Text input for ingestion
    st.subheader("Add Documents")
    input_text = st.text_area(
        "Paste your text or document content here:",
        height=150,
        placeholder="Enter text, notes, articles, or any content you want to learn from..."
    )
    
    if st.button("📤 Ingest Document", use_container_width=True, type="primary"):
        if input_text.strip():
            with st.spinner("Processing and storing document..."):
                try:
                    result = ingest_text(input_text)
                    st.session_state.ingested_chunks += result.get("chunks", 0)
                    st.success(f"✅ Document ingested! {result['chunks']} chunks stored.")
                except Exception as e:
                    st.error(f"❌ Error ingesting document: {str(e)}")
        else:
            st.warning("Please enter some text first.")
    
    st.divider()
    st.info(f"📊 Total chunks stored: {st.session_state.ingested_chunks}")

# Main chat interface
st.subheader("💬 Ask Questions")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything about your documents..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                response = generate_answer(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"❌ Error generating response: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.divider()
st.markdown(
    """
    ---
    **Second Brain** - Your personal knowledge assistant
    
    Built with 🔧 Streamlit, ChromaDB, LangChain, and Groq LLM
    """
)
