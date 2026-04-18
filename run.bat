@echo off
echo Starting Second Brain - Streamlit App...
echo.
echo Make sure you have:
echo 1. Installed dependencies: pip install -r backend/requirements.txt
echo 2. Set your GROQ_API_KEY in .env file
echo.
pause

streamlit run app.py
