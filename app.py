import streamlit as st
import os
import tempfile
from database import KnowledgeBase
from processor import FileProcessor
from query_engine import QueryEngine
from processors.audio_video_processor import AudioVideoProcessor
from config import GEMINI_API_KEY

# Page configuration
st.set_page_config(
    page_title="Multimodal Query System",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'db' not in st.session_state:
    st.session_state.db = KnowledgeBase()
if 'processor' not in st.session_state:
    st.session_state.processor = FileProcessor(st.session_state.db)
if 'query_engine' not in st.session_state:
    try:
        st.session_state.query_engine = QueryEngine(st.session_state.db)
    except Exception as e:
        st.session_state.query_engine = None
        st.session_state.api_key_error = str(e)

# Main title
st.title("🤖 Multimodal Query System")
st.markdown("Upload files or provide YouTube links, then ask questions about your content!")

# Check API key
if not GEMINI_API_KEY:
    st.error("⚠️ GEMINI_API_KEY not found. Please create a `.env` file with your API key.")
    st.info("Get your API key from: https://makersuite.google.com/app/apikey")
    st.stop()

if st.session_state.query_engine is None:
    st.error(f"Error initializing query engine: {st.session_state.get('api_key_error', 'Unknown error')}")
    st.info("💡 Tip: Make sure your GEMINI_API_KEY is correct and the model is available.")
    if st.button("🔄 Retry Initialization"):
        try:
            st.session_state.query_engine = QueryEngine(st.session_state.db)
            st.session_state.api_key_error = None
            st.success("✅ Query engine initialized successfully!")
            st.rerun()
        except Exception as e:
            st.session_state.api_key_error = str(e)
            st.error(f"Retry failed: {e}")
    st.stop()

# Sidebar for file management
with st.sidebar:
    st.header("📁 File Management")
    
    # File upload
    st.subheader("Upload Files")
    uploaded_files = st.file_uploader(
        "Choose files to process",
        type=['pdf', 'docx', 'pptx', 'md', 'txt', 'png', 'jpg', 'jpeg', 'mp3', 'mp4'],
        accept_multiple_files=True
    )
    
    # YouTube URL input
    st.subheader("YouTube Video")
    youtube_url = st.text_input("Enter YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    
    # Process button
    if st.button("🔄 Process Files", type="primary"):
        if uploaded_files or youtube_url:
            with st.spinner("Processing files..."):
                # Process uploaded files
                for uploaded_file in uploaded_files:
                    # Save uploaded file to temporary location
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                        tmp_file.write(uploaded_file.getbuffer())
                        tmp_path = tmp_file.name
                    
                    # Process file
                    result = st.session_state.processor.process_file(tmp_path, uploaded_file.name)
                    
                    if result['success']:
                        st.success(f"✅ {result['message']}")
                    else:
                        st.error(f"❌ {result['message']}")
                    
                    # Clean up temp file
                    os.unlink(tmp_path)
                
                # Process YouTube URL
                if youtube_url:
                    av_processor = AudioVideoProcessor()
                    if av_processor.is_youtube_url(youtube_url):
                        result = st.session_state.processor.process_youtube(youtube_url)
                        if result['success']:
                            st.success(f"✅ {result['message']}")
                        else:
                            st.error(f"❌ {result['message']}")
                    else:
                        st.error("Invalid YouTube URL")
        else:
            st.warning("Please upload files or provide a YouTube URL")
    
    # Show processed files
    st.subheader("Processed Files")
    files = st.session_state.db.get_all_files()
    if files:
        for file_info in files:
            status = "✅" if file_info['processed'] else "⏳"
            st.text(f"{status} {file_info['filename']}")
    else:
        st.info("No files processed yet")
    
    # Clear database button
    col1, col2 = st.columns(2)
    with col1:
        confirm = st.checkbox("Confirm deletion")
    with col2:
        if st.button("🗑️ Clear All Data", type="secondary", disabled=not confirm):
            try:
                st.session_state.db.clear_all_data()
                if os.path.exists("knowledge_base.db"):
                    os.remove("knowledge_base.db")
                st.session_state.db = KnowledgeBase()
                st.session_state.processor = FileProcessor(st.session_state.db)
                st.session_state.query_engine = QueryEngine(st.session_state.db)
                st.success("✅ Database cleared successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error clearing database: {e}")

# Main content area
st.header("💬 Ask Questions")

# Query input
query = st.text_input(
    "Enter your question",
    placeholder="What is the main topic of the documents?",
    key="query_input"
)

# Query button
if st.button("🔍 Search", type="primary") or query:
    if query:
        with st.spinner("Searching knowledge base..."):
            # Get response from query engine
            response = st.session_state.query_engine.query(query)
            
            # Display response
            st.subheader("Answer")
            st.write(response)
            
            # Save query to database
            st.session_state.db.save_query(query, response)
            
            # Show relevant chunks
            with st.expander("📄 View Relevant Context"):
                relevant_chunks = st.session_state.query_engine._get_relevant_chunks(query, limit=5)
                for i, chunk in enumerate(relevant_chunks, 1):
                    st.markdown(f"**Chunk {i} from {chunk.get('filename', 'Unknown')}:**")
                    content = chunk.get('content', '')
                    
                    # Handle JSON string content
                    if isinstance(content, str):
                        try:
                            import json
                            content = json.loads(content)
                        except (json.JSONDecodeError, TypeError):
                            pass
                    
                    if isinstance(content, dict):
                        content = content.get('ocr_text', '[Image content]')
                    
                    content_str = str(content)
                    st.text(content_str[:500] + "..." if len(content_str) > 500 else content_str)
                    st.divider()
    else:
        st.warning("Please enter a question")

# Statistics section
st.header("📊 Statistics")
col1, col2, col3 = st.columns(3)

with col1:
    files = st.session_state.db.get_all_files()
    st.metric("Total Files", len(files))

with col2:
    chunks = st.session_state.db.get_all_chunks()
    st.metric("Total Chunks", len(chunks))

with col3:
    processed_files = sum(1 for f in files if f['processed'])
    st.metric("Processed Files", processed_files)

# Instructions
with st.expander("ℹ️ How to Use"):
    st.markdown("""
    ### Getting Started
    
    1. **Upload Files**: Use the sidebar to upload files (PDF, DOCX, PPTX, MD, TXT, PNG, JPG, MP3, MP4)
    2. **Add YouTube Videos**: Paste a YouTube URL in the sidebar
    3. **Process**: Click "Process Files" to extract content
    4. **Query**: Ask questions about your documents in natural language
    5. **Get Answers**: Receive AI-powered answers based on your content
    
    ### Supported File Types
    
    - **Text**: PDF, DOCX, PPTX, MD, TXT
    - **Images**: PNG, JPG (with OCR)
    - **Audio**: MP3
    - **Video**: MP4, YouTube links
    
    ### Tips
    
    - Process multiple files to build a comprehensive knowledge base
    - Ask specific questions for better results
    - The system searches through all processed content
    - Image content is extracted using OCR and vision AI
    """)

