import os
import yt_dlp
import requests
from typing import List, Dict
import subprocess
import tempfile
import speech_recognition as sr
from pydub import AudioSegment

class AudioVideoProcessor:
    """Process audio and video files, including YouTube links"""
    
    @staticmethod
    def process_youtube(url: str) -> List[Dict]:
        """Download and process YouTube video"""
        chunks = []
        try:
            # Create temporary directory for downloads
            temp_dir = tempfile.mkdtemp()
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }
            
            # Extract video info
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown')
                description = info.get('description', '')
                duration = info.get('duration', 0)
                
                # Download audio
                ydl.download([url])
                
                # Find downloaded file
                downloaded_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
                if downloaded_files:
                    audio_path = os.path.join(temp_dir, downloaded_files[0])
                    
                    # Extract audio to text
                    text_content = AudioVideoProcessor._audio_to_text(audio_path)
                    
                    # Combine metadata and transcript
                    full_content = f"Title: {title}\nDescription: {description}\n\nTranscript:\n{text_content}"
                    
                    chunks.append({
                        "content": full_content,
                        "metadata": {
                            "source": "youtube",
                            "url": url,
                            "title": title,
                            "duration": duration
                        }
                    })
                    
                    # Clean up
                    os.remove(audio_path)
            
            os.rmdir(temp_dir)
            
        except Exception as e:
            print(f"Error processing YouTube: {e}")
            chunks = [{
                "content": f"Error processing YouTube video: {str(e)}",
                "metadata": {"source": "youtube", "url": url}
            }]
        
        return chunks
    
    @staticmethod
    def process_audio(file_path: str) -> List[Dict]:
        """Process audio file (MP3)"""
        chunks = []
        try:
            # Convert audio to text
            text_content = AudioVideoProcessor._audio_to_text(file_path)
            
            if text_content:
                chunks.append({
                    "content": text_content,
                    "metadata": {
                        "source": "audio",
                        "file_path": file_path,
                        "file_type": os.path.splitext(file_path)[1]
                    }
                })
            else:
                chunks.append({
                    "content": "No speech detected in audio file",
                    "metadata": {"source": "audio", "file_path": file_path}
                })
                
        except Exception as e:
            print(f"Error processing audio: {e}")
            chunks = [{
                "content": f"Error processing audio: {str(e)}",
                "metadata": {"source": "audio", "file_path": file_path}
            }]
        
        return chunks
    
    @staticmethod
    def process_video(file_path: str) -> List[Dict]:
        """Process video file (MP4)"""
        chunks = []
        try:
            # Extract audio from video
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_audio_path = temp_audio.name
            temp_audio.close()
            
            try:
                # Use ffmpeg to extract audio (if available)
                subprocess.run([
                    'ffmpeg', '-i', file_path, '-vn', '-acodec', 'pcm_s16le',
                    '-ar', '16000', '-ac', '1', '-y', temp_audio_path
                ], check=True, capture_output=True)
                
                # Convert audio to text
                text_content = AudioVideoProcessor._audio_to_text(temp_audio_path)
                
                if text_content:
                    chunks.append({
                        "content": text_content,
                        "metadata": {
                            "source": "video",
                            "file_path": file_path,
                            "file_type": "mp4"
                        }
                    })
                else:
                    chunks.append({
                        "content": "No speech detected in video file",
                        "metadata": {"source": "video", "file_path": file_path}
                    })
                    
            finally:
                # Clean up temporary audio file
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
                    
        except subprocess.CalledProcessError:
            # FFmpeg not available or failed, try direct processing
            chunks.append({
                "content": "Video processing requires ffmpeg. Please install ffmpeg to process video files.",
                "metadata": {"source": "video", "file_path": file_path}
            })
        except Exception as e:
            print(f"Error processing video: {e}")
            chunks = [{
                "content": f"Error processing video: {str(e)}",
                "metadata": {"source": "video", "file_path": file_path}
            }]
        
        return chunks
    
    @staticmethod
    def _audio_to_text(audio_path: str) -> str:
        """Convert audio file to text using speech recognition"""
        try:
            # Convert to WAV if needed
            audio = AudioSegment.from_file(audio_path)
            wav_path = audio_path
            if not audio_path.endswith('.wav'):
                wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
                audio.export(wav_path, format="wav")
            
            # Use speech recognition
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)
            
            # Try Google Speech Recognition (free, but requires internet)
            try:
                text = recognizer.recognize_google(audio_data)
                return text
            except sr.UnknownValueError:
                return "Could not understand audio"
            except sr.RequestError as e:
                # Fallback to offline recognition if available
                try:
                    text = recognizer.recognize_sphinx(audio_data)
                    return text
                except:
                    return f"Speech recognition error: {str(e)}"
            
        except Exception as e:
            print(f"Error in audio to text conversion: {e}")
            return f"Error converting audio: {str(e)}"
    
    @staticmethod
    def process_file(file_path: str) -> List[Dict]:
        """Process an audio/video file based on its extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.mp3':
            return AudioVideoProcessor.process_audio(file_path)
        elif ext == '.mp4':
            return AudioVideoProcessor.process_video(file_path)
        else:
            return [{
                "content": f"Unsupported audio/video type: {ext}",
                "metadata": {}
            }]
    
    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """Check if URL is a YouTube link"""
        youtube_domains = ['youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com']
        return any(domain in url.lower() for domain in youtube_domains)

