"""Video processing service for extracting audio and metadata."""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any
import json
import tempfile


class VideoProcessor:
    """Service for processing video files."""

    async def extract_audio(self, video_path: Path) -> Path:
        """
        Extract audio from video file using ffmpeg.
        
        Args:
            video_path: Path to the input video file
            
        Returns:
            Path to the extracted audio file
        """
        audio_path = video_path.parent / f"{video_path.stem}_audio.wav"
        
        # Use ffmpeg to extract audio
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # Audio codec
            "-ar", "16000",  # Sample rate
            "-ac", "1",  # Mono channel
            "-y",  # Overwrite output files
            str(audio_path)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")
                
            if not audio_path.exists():
                raise RuntimeError("Audio extraction failed - output file not created")
                
            return audio_path
            
        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg not found. Please install ffmpeg: "
                "brew install ffmpeg (macOS) or apt-get install ffmpeg (Ubuntu)"
            )
    
    async def get_video_info(self, video_path: Path) -> Dict[str, Any]:
        """
        Get video metadata using ffprobe.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing video metadata
        """
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"FFprobe failed: {stderr.decode()}")
            
            metadata = json.loads(stdout.decode())
            
            # Extract useful information
            format_info = metadata.get("format", {})
            video_stream = None
            audio_stream = None
            
            for stream in metadata.get("streams", []):
                if stream.get("codec_type") == "video" and not video_stream:
                    video_stream = stream
                elif stream.get("codec_type") == "audio" and not audio_stream:
                    audio_stream = stream
            
            return {
                "duration": float(format_info.get("duration", 0)),
                "size": int(format_info.get("size", 0)),
                "bitrate": int(format_info.get("bit_rate", 0)),
                "format_name": format_info.get("format_name", ""),
                "video": {
                    "codec": video_stream.get("codec_name", "") if video_stream else "",
                    "width": video_stream.get("width", 0) if video_stream else 0,
                    "height": video_stream.get("height", 0) if video_stream else 0,
                    "fps": self._parse_fps(video_stream.get("r_frame_rate", "0/1")) if video_stream else 0
                },
                "audio": {
                    "codec": audio_stream.get("codec_name", "") if audio_stream else "",
                    "sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream else 0,
                    "channels": audio_stream.get("channels", 0) if audio_stream else 0
                }
            }
            
        except FileNotFoundError:
            raise RuntimeError(
                "FFprobe not found. Please install ffmpeg: "
                "brew install ffmpeg (macOS) or apt-get install ffmpeg (Ubuntu)"
            )
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse video metadata: {e}")
    
    def _parse_fps(self, fps_string: str) -> float:
        """Parse fps from ffprobe format like '30/1' or '29.97'."""
        try:
            if "/" in fps_string:
                num, den = fps_string.split("/")
                return float(num) / float(den) if float(den) != 0 else 0
            return float(fps_string)
        except (ValueError, ZeroDivisionError):
            return 0.0
