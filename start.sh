#!/usr/bin/env bash
# Quick start script for Second Brain + YouTube Summarizer
# For Windows PowerShell, run: streamlit run app.py

echo "=================================="
echo "🚀 Starting Second Brain RAG App"
echo "=================================="
echo ""

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

# Check .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Please create .env file with: GROQ_API_KEY=your_key_here"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📦 Checking dependencies..."
python -m pip install -q -r backend/requirements.txt 2>/dev/null

echo ""
echo "🚀 Starting Streamlit app..."
echo "   🏠 Home: http://localhost:8501"
echo "   📄 Pages:"
echo "      - Second Brain (home)"
echo "      - YouTube Summarizer"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python -m streamlit run app.py
