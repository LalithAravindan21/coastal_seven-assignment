import os
from PIL import Image
from typing import List, Dict
import base64
import io

# Try to import pytesseract, but make it optional
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    pytesseract = None

class ImageProcessor:
    """Process image files using OCR and vision capabilities"""
    
    @staticmethod
    def process_image(file_path: str, use_ocr: bool = True) -> List[Dict]:
        """Process an image file"""
        chunks = []
        try:
            # Open and validate image
            image = Image.open(file_path)
            
            # Get image metadata
            metadata = {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.width,
                "height": image.height
            }
            
            # Extract text using OCR if enabled and available
            ocr_text = ""
            if use_ocr and OCR_AVAILABLE:
                try:
                    ocr_text = pytesseract.image_to_string(image)
                    ocr_text = ocr_text.strip()
                except Exception as e:
                    # OCR not available or failed - continue without it
                    # Gemini Vision API can still process the image
                    print(f"OCR error: {e}. Image will be processed using Gemini Vision API.")
                    ocr_text = ""
            elif use_ocr and not OCR_AVAILABLE:
                # OCR library not installed
                print("OCR not available (pytesseract not installed). Image will be processed using Gemini Vision API.")
                ocr_text = ""
            
            # Prepare image data for Gemini Vision API
            # Convert image to base64
            image_data = ImageProcessor._image_to_base64(image)
            
            # Store both OCR text and image data
            content = {
                "ocr_text": ocr_text,
                "image_base64": image_data,
                "has_text": bool(ocr_text)
            }
            
            chunks.append({
                "content": content,
                "metadata": metadata
            })
            
        except Exception as e:
            print(f"Error processing image: {e}")
            chunks = [{
                "content": {"ocr_text": f"Error reading image: {str(e)}", "image_base64": None, "has_text": False},
                "metadata": {}
            }]
        
        return chunks
    
    @staticmethod
    def _image_to_base64(image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            image_bytes = buffer.getvalue()
            
            # Encode to base64
            base64_str = base64.b64encode(image_bytes).decode('utf-8')
            return base64_str
        except Exception as e:
            print(f"Error converting image to base64: {e}")
            return ""
    
    @staticmethod
    def process_file(file_path: str) -> List[Dict]:
        """Process an image file based on its extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.png', '.jpg', '.jpeg']:
            return ImageProcessor.process_image(file_path)
        else:
            return [{
                "content": {"ocr_text": f"Unsupported image type: {ext}", "image_base64": None, "has_text": False},
                "metadata": {}
            }]

