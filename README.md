# 🧠 Second Brain - RAG System

A personal knowledge assistant built with Streamlit with multiple RAG capabilities:
- 📚 **Second Brain**: Learn from your documents and ask questions
- 🎥 **YouTube Summarizer**: Extract insights from YouTube videos

## 📋 Project Structure

```
├── app.py                      # Home page - Second Brain RAG
├── pages/
│   └── youtube_summarizer.py  # YouTube video analyzer
├── backend/
│   ├── db.py                  # ChromaDB setup (Second Brain)
│   ├── ingest.py              # Document ingestion
│   ├── search.py              # Vector search
│   ├── rag.py                 # RAG pipeline with Groq LLM
│   ├── youtube_rag.py         # YouTube RAG pipeline
│   └── requirements.txt        # Python dependencies
├── chroma_db/                 # Vector database (Second Brain)
├── chroma_youtube/            # Vector database (YouTube)
├── README.md                  # Main documentation
└── YOUTUBE_SUMMARIZER_GUIDE.md  # YouTube feature guide
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Groq API key (get it from [console.groq.com](https://console.groq.com))

### Installation

1. **Clone/Navigate to the project directory:**
   ```bash
   cd path/to/Hackathon(1)
   ```

2. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

### Running the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 🎯 Features

### 📚 Second Brain (Home Page)
- **Document Ingestion**: Upload and store your text documents, notes, and articles
- **Semantic Search**: Automatically finds relevant documents using embeddings
- **Chat Interface**: Ask questions and get answers based on your documents
- **Persistent Storage**: All ingested documents are stored locally in ChromaDB
- **User-Friendly UI**: Clean, intuitive Streamlit interface

### 🎥 YouTube Summarizer (Pages → YouTube Summarizer)
- **Transcript Extraction**: Automatically fetch transcripts from any YouTube video
- **Smart Q&A**: Ask questions about video content
- **Source References**: View exact excerpts from the video
- **Multi-Video Support**: Load and analyze different videos
- **Semantic Understanding**: Deep comprehension using advanced embeddings

## 🛠️ How It Works

1. **Ingestion**: Documents are split into chunks and converted to embeddings using `sentence-transformers`
2. **Storage**: Embeddings and text chunks are stored in ChromaDB
3. **Retrieval**: When you ask a question, it's converted to an embedding and similar chunks are retrieved
4. **Generation**: The Groq LLM generates an answer based on retrieved context

## 📦 Key Dependencies

- **Streamlit**: Web UI framework
- **ChromaDB**: Vector database for embeddings
- **LangChain**: LLM orchestration framework
- **Groq**: Fast LLM API
- **sentence-transformers**: Embedding model
- **python-dotenv**: Environment variable management

## 🔑 API Keys

This application requires a Groq API key:
1. Visit [console.groq.com](https://console.groq.com)
2. Create an account and generate an API key
3. Add it to your `.env` file as `GROQ_API_KEY`

## 📝 Usage

### Second Brain (Home Page)
1. **Add Documents**:
   - Paste text in the "Add Documents" section on the sidebar
   - Click "📤 Ingest Document" to store it

2. **Ask Questions**:
   - Type your question in the chat input
   - The assistant will search your documents and provide an answer

3. **Chat History**:
   - Your conversation history is maintained during the session
   - Refresh the page to clear history

### YouTube Summarizer (Pages → YouTube Summarizer)
1. **Load a Video**:
   - Enter a YouTube URL or video ID in the sidebar
   - Click "🔗 Fetch Transcript"
   - Wait for the AI model to process the video

2. **Ask Questions**:
   - Type questions about the video content
   - Get AI-powered answers with source references
   - View transcript excerpts for context

3. **View Transcript**:
   - Click on "View Full Transcript" to see the complete video text
   - Each answer shows relevant source snippets

See [YOUTUBE_SUMMARIZER_GUIDE.md](YOUTUBE_SUMMARIZER_GUIDE.md) for detailed YouTube feature documentation.

## ⚙️ Configuration

### Chunk Size
Edit `backend/ingest.py` to change document chunk size (default: 500 words)

### Embedding Model
Edit `backend/db.py` to use a different embedding model:
```python
model = SentenceTransformer('all-MiniLM-L6-v2')  # Default
# Other options: 'all-mpnet-base-v2', 'paraphrase-MiniLM-L6-v2', etc.
```

### LLM Model
Edit `backend/rag.py` to change the Groq model:
```python
model_name="llama3-8b-8192"  # Default
# Other options: "mixtral-8x7b-32768", "gemma-7b-it", etc.
```

## 🐛 Troubleshooting

### Issue: "GROQ_API_KEY not found"
- **Solution**: Ensure `.env` file exists in the project root with your API key

### Issue: "ChromaDB connection error"
- **Solution**: Delete `chroma_db/` folder and restart the app to reinitialize the database

### Issue: Slow embedding generation
- **Solution**: This is normal on first run. The embedding model is downloaded. Subsequent queries will be faster.

## 📄 License

MIT License - Feel free to use and modify for your needs

## 🤝 Contributing

Contributions are welcome! Feel free to submit issues and pull requests.
