#!/usr/bin/env python3
"""
Second Brain - RAG System Launcher
Run this script to start the Streamlit application
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("=" * 60)
    print("🧠 Second Brain - RAG System Launcher")
    print("=" * 60)
    print()
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  WARNING: .env file not found!")
        print("   Please create a .env file with your GROQ_API_KEY")
        print("   You can copy from .env.example and add your key")
        print()
        response = input("Continue anyway? (y/n): ").lower()
        if response != 'y':
            sys.exit(1)
    
    # Check if requirements are installed
    print("📦 Checking dependencies...")
    try:
        import streamlit
        import chromadb
        import langchain
        print("✅ All dependencies are installed!")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\n📥 Installing dependencies...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"],
            check=True
        )
        print("✅ Dependencies installed!")
    
    print()
    print("🚀 Starting Streamlit application...")
    print("   App will open at: http://localhost:8501")
    print()
    
    # Run streamlit
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])

if __name__ == "__main__":
    main()
