# 🎥 YouTube Video Summarizer Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install --upgrade -r backend/requirements.txt
```

### 2. Run the App
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

### 3. Navigate to YouTube Summarizer
Once the app loads, you'll see a sidebar menu with:
- **Home** - Second Brain (Document RAG)
- **YouTube Summarizer** - Click here for YouTube video analysis

## Features

✅ **Extract YouTube Transcripts**
- Supports full URLs: `https://www.youtube.com/watch?v=...`
- Supports short URLs: `https://youtu.be/...`
- Supports video IDs: Just paste the ID

✅ **AI-Powered Q&A**
- Ask questions about video content
- Get answers based on transcript
- View source references

✅ **Smart Chunking**
- Transcript split into optimal chunks (1000 chars, 200 overlap)
- Better context preservation
- Semantic search with top-5 retrieval

✅ **Vector Embeddings**
- Uses `intfloat/e5-large-v2` for high-quality embeddings
- Persistent storage in ChromaDB
- Fast similarity search

✅ **Groq LLM Integration**
- Uses `gemma2-9b-it` model for fast inference
- Temperature: 0.1 (focused, accurate responses)
- Max tokens: 1024 per response

## Usage Example

1. **Load a Video**
   - Paste: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
   - Click "🔗 Fetch Transcript"
   - Wait for processing (shows chunk count when ready)

2. **Ask Questions**
   - Type: "What is the main topic of this video?"
   - Get AI-powered answer with source excerpts
   - View transcript snippets in expandable sections

3. **View Transcript**
   - Click "📄 View Full Transcript" to see the complete video text
   - References shown in chat for context

## Environment Setup

Make sure `.env` file has:
```
GROQ_API_KEY=your_groq_api_key_here
```

Get your key from [console.groq.com](https://console.groq.com)

## Storage

- Transcripts: Stored in `chroma_youtube/` directory
- Persistent storage allows reusing previous videos
- Clear the folder to start fresh

## Troubleshooting

**Issue: "Video not found"**
- Ensure the video ID/URL is correct
- Check if the video has captions/transcripts enabled

**Issue: "Slow processing"**
- First run downloads the embedding model (~500MB)
- Subsequent queries will be faster

**Issue: "API rate limit"**
- Wait a moment and try again
- Check your Groq API quota

## Architecture

```
pages/youtube_summarizer.py      # Streamlit UI
    ↓
backend/youtube_rag.py            # RAG Logic
    ↓
YouTube Transcript API            # Fetch transcripts
    ↓
LangChain                          # Text splitting
    ↓
HuggingFace Embeddings            # Vector embeddings
    ↓
ChromaDB                           # Vector store
    ↓
Groq LLM (gemma2-9b-it)           # Answer generation
```

## Advanced Configuration

### Change Embedding Model
Edit `backend/youtube_rag.py`:
```python
EMBED_MODEL = "intfloat/e5-large-v2"  # Default
# Other options: "all-mpnet-base-v2", "sentence-transformers/all-MiniLM-L6-v2"
```

### Change LLM Model
Edit `backend/youtube_rag.py`:
```python
model_name="gemma2-9b-it"  # Default
# Other options: "mixtral-8x7b-32768", "llama3-8b-8192"
```

### Adjust Chunk Size
Edit `backend/youtube_rag.py`:
```python
chunk_size=1000,      # Size of each text chunk
chunk_overlap=200,    # Overlap between chunks
```

## API Requirements

- **Groq API**: Free tier available at console.groq.com
- **HuggingFace**: Embeddings work offline after first download
- **YouTube**: Video must have captions/transcripts enabled

## Performance Tips

1. **Faster Responses**: Use smaller embedding models (`all-MiniLM-L6-v2`)
2. **Better Quality**: Use larger models (`all-mpnet-base-v2`)
3. **More Context**: Increase `search_kwargs={"k": 5}` to retrieve more chunks
4. **Faster First Load**: Models download on first use (~1-2 minutes)
