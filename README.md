# Multimodal Query System

A system that processes various file types (text, images, audio, video) and answers natural language queries using Google's Gemini AI.

## Features

- **Text Processing**: PDF, DOCX, PPTX, MD, TXT
- **Image Processing**: PNG, JPG (OCR + Vision)
- **Audio/Video Processing**: MP3, MP4, YouTube links
- **Natural Language Queries**: Ask questions about your documents
- **Streamlit UI**: User-friendly web interface

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Google Gemini API:
   - Get your free API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
   - The system uses `gemini-1.5-flash` by default (free tier, fast responses)
   - You can modify `config.py` to use other models like `gemini-1.5-pro` for better quality

3. Run the application:
```bash
streamlit run app.py
```

## Usage

### Streamlit UI (Recommended)

1. Run the application:
```bash
streamlit run app.py
```

2. Upload files or provide YouTube links in the sidebar
3. Click "Process Files" to extract content
4. Ask questions about your documents in natural language
5. Get AI-powered answers based on your content

### Command Line Interface

You can also use the CLI for processing and querying:

```bash
# Process a file
python cli.py process document.pdf

# Process a YouTube video
python cli.py process "https://www.youtube.com/watch?v=..."

# Query the knowledge base
python cli.py query "What is the main topic?"

# List all processed files
python cli.py list

# Clear all data
python cli.py clear --confirm
```

## File Structure

- `app.py` - Main Streamlit application
- `cli.py` - Command-line interface
- `processor.py` - Main file processing pipeline
- `processors/` - File processing modules
  - `text_processor.py` - Text file processing (PDF, DOCX, PPTX, MD, TXT)
  - `image_processor.py` - Image processing with OCR
  - `audio_video_processor.py` - Audio/video and YouTube processing
- `database.py` - SQLite database management
- `query_engine.py` - Query processing with Gemini AI
- `config.py` - Configuration settings

## Optional Dependencies

Some features require additional setup:

- **OCR for Images**: Requires Tesseract OCR installed on your system
  - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
  - Mac: `brew install tesseract`
  - Linux: `sudo apt-get install tesseract-ocr`

- **Video Processing**: Requires FFmpeg for MP4 files
  - Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)
  - Mac: `brew install ffmpeg`
  - Linux: `sudo apt-get install ffmpeg`

Note: The system will work without these, but some features may be limited.

