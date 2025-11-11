# Quick Start Guide

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Set Up API Key

1. Get your free Gemini API key from: https://makersuite.google.com/app/apikey
2. Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

## 3. Run the Application

### Option A: Streamlit UI (Recommended)
```bash
streamlit run app.py
```
Then open your browser to the URL shown (usually http://localhost:8501)

### Option B: Command Line
```bash
# Process a file
python cli.py process sample.pdf

# Ask a question
python cli.py query "What is this document about?"
```

## 4. Test with Sample Files

Try uploading:
- A PDF document
- A Word document (.docx)
- An image with text (PNG/JPG)
- A YouTube video URL

Then ask questions like:
- "What is the main topic?"
- "Summarize the key points"
- "What are the important dates mentioned?"

## Troubleshooting

### API Key Issues
- Make sure `.env` file exists in the project root
- Verify the API key is correct (no extra spaces)
- Check that you've enabled the Gemini API in Google Cloud Console

### OCR Not Working
- Install Tesseract OCR (see README.md)
- Images will still work with Gemini Vision API even without OCR

### Video Processing Issues
- Install FFmpeg for MP4 processing (see README.md)
- YouTube videos should work without FFmpeg

### Import Errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Use Python 3.8 or higher

