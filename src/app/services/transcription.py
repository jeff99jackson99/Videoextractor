"""Transcription service using OpenAI Whisper."""

import os
from pathlib import Path
from typing import Optional
import openai
from openai import OpenAI


class TranscriptionService:
    """Service for transcribing audio to text using OpenAI Whisper."""

    def __init__(self):
        """Initialize the transcription service."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required for transcription"
            )
        self.client = OpenAI(api_key=api_key)

    async def transcribe_audio(self, audio_path: Path) -> str:
        """
        Transcribe audio file to text using OpenAI Whisper.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcribed text
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            return transcript if isinstance(transcript, str) else transcript.text
            
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {str(e)}")

    async def transcribe_with_timestamps(self, audio_path: Path) -> dict:
        """
        Transcribe audio with timestamps using OpenAI Whisper.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dictionary with transcript and timestamp information
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["word", "segment"]
                )
            
            return {
                "text": transcript.text,
                "language": transcript.language,
                "duration": transcript.duration,
                "words": transcript.words if hasattr(transcript, 'words') else [],
                "segments": transcript.segments if hasattr(transcript, 'segments') else []
            }
            
        except Exception as e:
            raise RuntimeError(f"Transcription with timestamps failed: {str(e)}")

    def format_transcript_with_timestamps(self, transcript_data: dict) -> str:
        """
        Format transcript with timestamps for better readability.
        
        Args:
            transcript_data: Dictionary from transcribe_with_timestamps
            
        Returns:
            Formatted transcript string
        """
        if not transcript_data.get("segments"):
            return transcript_data.get("text", "")
        
        formatted_lines = []
        for segment in transcript_data["segments"]:
            start_time = self._format_time(segment.get("start", 0))
            end_time = self._format_time(segment.get("end", 0))
            text = segment.get("text", "").strip()
            
            formatted_lines.append(f"[{start_time} - {end_time}] {text}")
        
        return "\n".join(formatted_lines)

    def _format_time(self, seconds: float) -> str:
        """Format seconds to MM:SS format."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
