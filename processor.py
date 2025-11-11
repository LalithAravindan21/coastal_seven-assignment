import os
import json
from typing import List, Dict
from database import KnowledgeBase
from processors.text_processor import TextProcessor
from processors.image_processor import ImageProcessor
from processors.audio_video_processor import AudioVideoProcessor
from config import ALLOWED_EXTENSIONS

class FileProcessor:
    """Main file processing pipeline"""
    
    def __init__(self, db: KnowledgeBase):
        self.db = db
        self.text_processor = TextProcessor()
        self.image_processor = ImageProcessor()
        self.audio_video_processor = AudioVideoProcessor()
    
    def get_file_type(self, file_path: str) -> str:
        """Determine file type from extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ALLOWED_EXTENSIONS['text']:
            return 'text'
        elif ext in ALLOWED_EXTENSIONS['image']:
            return 'image'
        elif ext in ALLOWED_EXTENSIONS['audio']:
            return 'audio'
        elif ext in ALLOWED_EXTENSIONS['video']:
            return 'video'
        else:
            return 'unknown'
    
    def process_file(self, file_path: str, filename: str = None) -> Dict:
        """Process a single file and store in database"""
        if filename is None:
            filename = os.path.basename(file_path)
        
        file_type = self.get_file_type(file_path)
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        # Add file to database
        file_id = self.db.add_file(filename, file_type, file_path, file_size)
        
        try:
            # Process based on file type
            chunks = []
            
            if file_type == 'text':
                chunks = self.text_processor.process_file(file_path)
                content_type = 'text'
            elif file_type == 'image':
                chunks = self.image_processor.process_file(file_path)
                content_type = 'image'
            elif file_type in ['audio', 'video']:
                chunks = self.audio_video_processor.process_file(file_path)
                content_type = 'audio_video'
            else:
                return {
                    'success': False,
                    'message': f'Unsupported file type: {file_type}',
                    'file_id': file_id
                }
            
            # Store chunks in database
            for idx, chunk in enumerate(chunks):
                content = chunk.get('content', '')
                metadata = chunk.get('metadata', {})
                
                # Convert content to string if it's a dict (for images)
                if isinstance(content, dict):
                    content_str = json.dumps(content)
                else:
                    content_str = str(content)
                
                self.db.add_chunk(file_id, idx, content_str, content_type, metadata)
            
            # Mark file as processed
            self.db.mark_file_processed(file_id)
            
            return {
                'success': True,
                'message': f'Successfully processed {filename}',
                'file_id': file_id,
                'chunks_count': len(chunks)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error processing file: {str(e)}',
                'file_id': file_id
            }
    
    def process_youtube(self, url: str) -> Dict:
        """Process a YouTube URL"""
        filename = f"YouTube: {url}"
        file_id = self.db.add_file(filename, 'youtube', url, 0)
        
        try:
            chunks = self.audio_video_processor.process_youtube(url)
            
            # Store chunks
            for idx, chunk in enumerate(chunks):
                content = chunk.get('content', '')
                metadata = chunk.get('metadata', {})
                
                self.db.add_chunk(file_id, idx, str(content), 'audio_video', metadata)
            
            self.db.mark_file_processed(file_id)
            
            return {
                'success': True,
                'message': f'Successfully processed YouTube video',
                'file_id': file_id,
                'chunks_count': len(chunks)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error processing YouTube video: {str(e)}',
                'file_id': file_id
            }

