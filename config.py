import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Updated model names - using available Gemini API models
# Available models: gemini-2.5-flash, gemini-2.0-flash, gemini-flash-latest, gemini-pro-latest
GEMINI_MODEL = "gemini-2.5-flash"  # For text (free tier, fast, latest stable)
GEMINI_VISION_MODEL = "gemini-2.5-flash"  # For images (supports multimodal)
# Alternative models: "gemini-2.0-flash", "gemini-flash-latest", "gemini-pro-latest"

# Database Configuration
DATABASE_PATH = "knowledge_base.db"

# File Upload Configuration
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {
    'text': ['.pdf', '.docx', '.pptx', '.md', '.txt'],
    'image': ['.png', '.jpg', '.jpeg'],
    'audio': ['.mp3'],
    'video': ['.mp4'],
    'youtube': ['youtube.com', 'youtu.be']
}

# Processing Configuration
CHUNK_SIZE = 1000  # Characters per chunk for text splitting
OVERLAP_SIZE = 200  # Overlap between chunks

