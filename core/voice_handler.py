"""
StudyMate Voice Handler - Advanced Speech Processing
Handles speech-to-text, text-to-speech, and voice interactions
"""

import os
import asyncio
import uuid
from pathlib import Path
from typing import Optional, Dict, List, Any
import requests
import json
from datetime import datetime

# Optional imports
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import soundfile as sf
    import librosa
    AUDIO_PROCESSING_AVAILABLE = True
except ImportError:
    AUDIO_PROCESSING_AVAILABLE = False

class VoiceHandler:
    """Advanced voice processing with multiple TTS/STT providers"""
    
    def __init__(self):
        print("🎤 Initializing Voice Handler...")
        
        # Configuration
        self.whisper_model_name = os.getenv("WHISPER_MODEL", "base")
        self.whisper_language = os.getenv("WHISPER_LANGUAGE", "auto")
        self.max_audio_size = int(os.getenv("MAX_AUDIO_SIZE_MB", 25)) * 1024 * 1024
        
        # ElevenLabs configuration
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.elevenlabs_url = "https://api.elevenlabs.io/v1"
        # Matilda voice ID from ElevenLabs (female voice)
        self.default_voice_id = os.getenv("DEFAULT_VOICE_ID", "XB0fDUnXU5powFXDhCwa")
        
        # Voice settings
        self.voice_settings = {
            "stability": float(os.getenv("VOICE_STABILITY", 0.5)),
            "similarity_boost": float(os.getenv("VOICE_SIMILARITY_BOOST", 0.5)),
            "style": float(os.getenv("VOICE_STYLE", 0.0))
        }
        
        # Storage
        self.audio_dir = Path("static/audio")
        self.temp_dir = Path("temp")
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Models (lazy loading)
        self._whisper_model = None
        self._available_voices = None
        
        # Capabilities
        self.available = WHISPER_AVAILABLE and bool(self.elevenlabs_api_key)
        
        print(f"✅ Voice Handler ready - Whisper: {WHISPER_AVAILABLE}, ElevenLabs: {bool(self.elevenlabs_api_key)}")
    
    async def transcribe_audio(
        self, 
        audio_path: str, 
        language: Optional[str] = None,
        options: Optional[Dict] = None
    ) -> str:
        """Advanced audio transcription with options"""
        
        if not WHISPER_AVAILABLE:
            return "Voice transcription not available. Install: pip install openai-whisper"
        
        try:
            # Validate audio file
            audio_file = Path(audio_path)
            if not audio_file.exists():
                return "Audio file not found"
            
            if audio_file.stat().st_size > self.max_audio_size:
                return f"Audio file too large. Max size: {self.max_audio_size // (1024*1024)}MB"
            
            # Load Whisper model if needed
            if self._whisper_model is None:
                print(f"📥 Loading Whisper model: {self.whisper_model_name}")
                self._whisper_model = whisper.load_model(self.whisper_model_name)
            
            # Transcription options
            transcribe_options = {
                "language": language or self.whisper_language,
                "task": "transcribe",
                "fp16": False  # Better compatibility
            }
            
            if options:
                transcribe_options.update(options)
            
            # Transcribe
            print(f"🎯 Transcribing audio: {audio_file.name}")
            result = self._whisper_model.transcribe(str(audio_path), **transcribe_options)
            
            transcription = result["text"].strip()
            
            # Enhanced result with metadata
            if options and options.get("include_metadata", False):
                return {
                    "text": transcription,
                    "language": result.get("language"),
                    "segments": result.get("segments", []),
                    "duration": self._get_audio_duration(audio_path)
                }
            
            return transcription
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return f"Transcription failed: {str(e)}"
    
    async def text_to_speech(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        language: str = "en",
        options: Optional[Dict] = None
    ) -> str:
        """Advanced text-to-speech with multiple options"""
        
        try:
            if not self.elevenlabs_api_key:
                return ""
            
            # Validate input
            if not text or len(text.strip()) == 0:
                return ""
            
            if len(text) > 5000:  # ElevenLabs limit
                text = text[:5000] + "..."
            
            voice_id = voice_id or self.default_voice_id
            
            # Prepare request
            url = f"{self.elevenlabs_url}/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_api_key
            }
            
            # Voice settings
            voice_settings = self.voice_settings.copy()
            if options and "voice_settings" in options:
                voice_settings.update(options["voice_settings"])
            
            data = {
                "text": text,
                "model_id": options.get("model_id", "eleven_monolingual_v1"),
                "voice_settings": voice_settings
            }
            
            # Add pronunciation dictionary if provided
            if options and "pronunciation_dictionary" in options:
                data["pronunciation_dictionary_locators"] = options["pronunciation_dictionary"]
            
            print(f"🔊 Generating speech for {len(text)} characters")
            
            # Make request
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Generate unique filename
                audio_id = str(uuid.uuid4())[:8]
                audio_filename = f"tts_{audio_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                audio_path = self.audio_dir / audio_filename
                
                # Save audio file
                with open(audio_path, "wb") as f:
                    f.write(response.content)
                
                print(f"✅ Generated speech: {audio_filename}")
                return str(audio_path)
            else:
                error_msg = f"ElevenLabs API error: {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('detail', response.text)}"
                    except:
                        error_msg += f" - {response.text}"
                
                print(f"❌ TTS Error: {error_msg}")
                return ""
                
        except Exception as e:
            print(f"❌ TTS generation error: {e}")
            return ""
    
    async def get_available_voices(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """Get available ElevenLabs voices with caching"""
        
        if not refresh and self._available_voices is not None:
            return self._available_voices
        
        try:
            if not self.elevenlabs_api_key:
                return []
            
            url = f"{self.elevenlabs_url}/voices"
            headers = {"xi-api-key": self.elevenlabs_api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                voices_data = response.json()
                voices = []
                
                for voice in voices_data.get("voices", []):
                    voice_info = {
                        "voice_id": voice["voice_id"],
                        "name": voice["name"],
                        "category": voice.get("category", "premade"),
                        "description": voice.get("description", ""),
                        "labels": voice.get("labels", {}),
                        "preview_url": voice.get("preview_url"),
                        "available_for_tiers": voice.get("available_for_tiers", [])
                    }
                    voices.append(voice_info)
                
                self._available_voices = voices
                print(f"📋 Loaded {len(voices)} available voices")
                return voices
            else:
                print(f"❌ Error fetching voices: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting voices: {e}")
            return []
    
    async def clone_voice(
        self, 
        name: str, 
        audio_files: List[str], 
        description: Optional[str] = None
    ) -> Optional[str]:
        """Clone a voice using ElevenLabs (requires subscription)"""
        
        try:
            if not self.elevenlabs_api_key:
                return None
            
            url = f"{self.elevenlabs_url}/voices/add"
            headers = {"xi-api-key": self.elevenlabs_api_key}
            
            # Prepare files
            files = []
            for i, audio_file in enumerate(audio_files):
                if Path(audio_file).exists():
                    files.append(('files', (f'audio_{i}.mp3', open(audio_file, 'rb'), 'audio/mpeg')))
            
            data = {
                'name': name,
                'description': description or f"Cloned voice: {name}"
            }
            
            response = requests.post(url, headers=headers, files=files, data=data)
            
            # Close file handles
            for _, file_tuple in files:
                file_tuple[1].close()
            
            if response.status_code == 200:
                result = response.json()
                voice_id = result.get("voice_id")
                print(f"✅ Voice cloned successfully: {voice_id}")
                return voice_id
            else:
                print(f"❌ Voice cloning failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Voice cloning error: {e}")
            return None
    
    async def get_voice_settings(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """Get optimal settings for a specific voice"""
        
        try:
            if not self.elevenlabs_api_key:
                return None
            
            url = f"{self.elevenlabs_url}/voices/{voice_id}/settings"
            headers = {"xi-api-key": self.elevenlabs_api_key}
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error getting voice settings: {e}")
            return None
    
    def _get_audio_duration(self, audio_path: str) -> Optional[float]:
        """Get audio file duration"""
        try:
            if AUDIO_PROCESSING_AVAILABLE:
                duration = librosa.get_duration(filename=audio_path)
                return duration
            else:
                # Fallback: estimate from file size (rough)
                file_size = Path(audio_path).stat().st_size
                # Rough estimate: 1 minute ≈ 1MB for compressed audio
                return file_size / (1024 * 1024) * 60
        except Exception as e:
            print(f"❌ Error getting audio duration: {e}")
            return None
    
    async def process_audio_file(
        self, 
        audio_path: str, 
        target_format: str = "wav",
        sample_rate: int = 16000
    ) -> Optional[str]:
        """Process and convert audio file"""
        
        try:
            if not AUDIO_PROCESSING_AVAILABLE:
                return audio_path  # Return original if no processing available
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=sample_rate)
            
            # Generate output path
            input_path = Path(audio_path)
            output_path = self.temp_dir / f"{input_path.stem}_processed.{target_format}"
            
            # Save processed audio
            sf.write(str(output_path), audio, sample_rate)
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Audio processing error: {e}")
            return audio_path
    
    async def cleanup_old_audio(self, max_files: int = 200, max_age_hours: int = 24):
        """Advanced cleanup with age and count limits"""
        
        try:
            from datetime import timedelta
            
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=max_age_hours)
            
            # Get all audio files
            audio_files = []
            for pattern in ["*.mp3", "*.wav", "*.m4a"]:
                audio_files.extend(list(self.audio_dir.glob(pattern)))
            
            # Sort by creation time
            audio_files.sort(key=lambda x: x.stat().st_ctime)
            
            files_to_remove = []
            
            # Remove old files
            for file_path in audio_files:
                file_time = datetime.fromtimestamp(file_path.stat().st_ctime)
                if file_time < cutoff_time:
                    files_to_remove.append(file_path)
            
            # Remove excess files (keep only max_files newest)
            if len(audio_files) > max_files:
                excess_files = audio_files[:-max_files]
                files_to_remove.extend(excess_files)
            
            # Remove duplicates
            files_to_remove = list(set(files_to_remove))
            
            # Delete files
            for file_path in files_to_remove:
                try:
                    file_path.unlink()
                except Exception as e:
                    print(f"❌ Error deleting {file_path}: {e}")
            
            if files_to_remove:
                print(f"🧹 Cleaned up {len(files_to_remove)} audio files")
            
            # Also cleanup temp directory
            temp_files = list(self.temp_dir.glob("*"))
            for temp_file in temp_files:
                try:
                    if temp_file.is_file():
                        file_age = datetime.now() - datetime.fromtimestamp(temp_file.stat().st_ctime)
                        if file_age.total_seconds() > 3600:  # 1 hour
                            temp_file.unlink()
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get voice usage statistics"""
        
        try:
            if not self.elevenlabs_api_key:
                return {"error": "API key not configured"}
            
            url = f"{self.elevenlabs_url}/user"
            headers = {"xi-api-key": self.elevenlabs_api_key}
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "character_count": user_data.get("subscription", {}).get("character_count", 0),
                    "character_limit": user_data.get("subscription", {}).get("character_limit", 0),
                    "can_extend_character_limit": user_data.get("subscription", {}).get("can_extend_character_limit", False),
                    "allowed_to_extend_character_limit": user_data.get("subscription", {}).get("allowed_to_extend_character_limit", False),
                    "next_character_count_reset_unix": user_data.get("subscription", {}).get("next_character_count_reset_unix", 0)
                }
            else:
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}