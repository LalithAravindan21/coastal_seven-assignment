import google.generativeai as genai
from typing import List, Dict
import json
import os
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_VISION_MODEL
from database import KnowledgeBase

class QueryEngine:
    """Process natural language queries using Gemini AI"""
    
    def __init__(self, db: KnowledgeBase):
        self.db = db
        self.model = None
        self.vision_model = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize Gemini models"""
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set. Please set it in .env file.")
        
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Try to initialize the model with fallbacks
        # Using models that are actually available in the API
        model_attempts = [
            GEMINI_MODEL,
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-flash-latest",
            "gemini-pro-latest"
        ]
        
        self.model = None
        for model_name in model_attempts:
            try:
                self.model = genai.GenerativeModel(model_name)
                print(f"Successfully initialized model: {model_name}")
                break
            except Exception as e:
                print(f"Failed to initialize {model_name}: {e}")
                continue
        
        if self.model is None:
            raise ValueError(
                f"Failed to initialize any Gemini model. Tried: {', '.join(model_attempts)}. "
                "Please check your API key and available models."
            )
        
        # Initialize vision model (same model supports multimodal)
        try:
            self.vision_model = genai.GenerativeModel(GEMINI_VISION_MODEL)
        except:
            # If vision model not available, use regular model
            self.vision_model = self.model
    
    def _get_relevant_chunks(self, query: str, limit: int = 10) -> List[Dict]:
        """Retrieve relevant chunks from database based on query"""
        # Simple keyword-based retrieval (can be enhanced with embeddings)
        all_chunks = self.db.get_all_chunks()
        
        # Filter chunks that might be relevant
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_chunks = []
        for chunk in all_chunks:
            content = chunk.get('content', '')
            
            # Handle content that might be stored as JSON string
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except (json.JSONDecodeError, TypeError):
                    pass  # Not JSON, use as string
            
            # Extract text for matching
            if isinstance(content, dict):
                # For images, use OCR text
                content_text = content.get('ocr_text', '').lower()
            else:
                content_text = str(content).lower()
            
            # Simple relevance scoring
            score = sum(1 for word in query_words if word in content_text)
            if score > 0:
                scored_chunks.append((score, chunk))
        
        # Sort by score and return top chunks
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_chunks[:limit]]
    
    def _prepare_context(self, chunks: List[Dict]) -> str:
        """Prepare context string from chunks"""
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            filename = chunk.get('filename', 'Unknown')
            content = chunk.get('content', '')
            
            # Handle content that might be stored as JSON string
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except (json.JSONDecodeError, TypeError):
                    pass  # Not JSON, use as string
            
            if isinstance(content, dict):
                # For images, use OCR text if available
                content_text = content.get('ocr_text', '')
                if not content_text:
                    content_text = "[Image content - visual information available]"
            else:
                content_text = str(content)
            
            context_parts.append(f"Document: {filename}\nContent:\n{content_text}\n")
        
        return "\n---\n".join(context_parts)
    
    def query(self, user_query: str) -> str:
        """Process a natural language query and return response"""
        try:
            # Get relevant chunks
            relevant_chunks = self._get_relevant_chunks(user_query, limit=10)
            
            if not relevant_chunks:
                return "I couldn't find any relevant information in the processed files. Please make sure you have uploaded and processed some files first."
            
            # Prepare context
            context = self._prepare_context(relevant_chunks)
            
            # Prepare prompt for Gemini
            prompt = f"""You are a helpful assistant that answers questions based on the provided context from various documents.

Context from documents:
{context}

User Question: {user_query}

Please provide a clear, accurate answer based on the context above. If the information is not available in the context, say so. If you need to reference specific documents, mention the document names.

Answer:"""
            
            # Generate response using Gemini
            try:
                response = self.model.generate_content(prompt)
                # Handle different response formats
                if hasattr(response, 'text'):
                    return response.text
                elif hasattr(response, 'candidates') and len(response.candidates) > 0:
                    return response.candidates[0].content.parts[0].text
                else:
                    return str(response)
            except Exception as api_error:
                error_msg = str(api_error)
                if "404" in error_msg or "not found" in error_msg.lower():
                    return f"Model error: The Gemini model is not available. Please check your API key and model configuration. Error: {error_msg}"
                elif "403" in error_msg or "permission" in error_msg.lower():
                    return f"API key error: Please check your GEMINI_API_KEY in the .env file. Error: {error_msg}"
                else:
                    return f"API error: {error_msg}"
            
        except Exception as e:
            error_msg = str(e)
            if "GEMINI_API_KEY" in error_msg:
                return f"Configuration error: {error_msg}. Please set your GEMINI_API_KEY in the .env file."
            return f"Error processing query: {error_msg}. Please check your configuration and try again."
    
    def query_with_images(self, user_query: str) -> str:
        """Process query that might involve images"""
        try:
            # Get all chunks including images
            all_chunks = self.db.get_all_chunks()
            
            # Separate text and image chunks
            text_chunks = []
            image_chunks = []
            
            for chunk in all_chunks:
                if isinstance(chunk.get('content'), dict) and chunk['content'].get('image_base64'):
                    image_chunks.append(chunk)
                else:
                    text_chunks.append(chunk)
            
            # Get relevant text chunks
            relevant_text = self._get_relevant_chunks(user_query, limit=5)
            
            # Prepare text context
            text_context = self._prepare_context(relevant_text)
            
            # If there are images and the query might be about them, include images
            if image_chunks and any(word in user_query.lower() for word in ['image', 'picture', 'photo', 'see', 'show', 'what', 'describe']):
                # Use vision model for image queries
                # For now, process text context first, then add image processing if needed
                prompt = f"""Based on the following context from documents, answer the user's question.

Text Context:
{text_context}

User Question: {user_query}

Answer:"""
                
                response = self.model.generate_content(prompt)
                return response.text
            else:
                # Regular text query
                return self.query(user_query)
                
        except Exception as e:
            return f"Error processing query with images: {str(e)}"

