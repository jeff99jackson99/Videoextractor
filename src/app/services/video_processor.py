"""Video processing service for extracting audio and metadata."""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple
import json
import tempfile


class VideoProcessor:
    """Service for processing video files."""

    def __init__(self):
        """Initialize video processor with configuration."""
        import os
        self.silence_threshold = os.getenv("SILENCE_THRESHOLD", "-30dB")  # Silence threshold
        self.silence_duration = os.getenv("SILENCE_DURATION", "0.5")     # Minimum silence duration to detect (seconds)
        self.audio_padding = os.getenv("AUDIO_PADDING", "0.2")        # Padding around speech segments (seconds)

    async def extract_audio_with_silence_removal(self, video_path: Path) -> Path:
        """
        Extract audio from video and remove silence segments for efficient processing.
        
        Args:
            video_path: Path to the input video file
            
        Returns:
            Path to the processed audio file with silence removed
        """
        # First extract raw audio
        raw_audio_path = await self.extract_audio(video_path)
        
        # Detect silence segments
        silence_segments = await self.detect_silence(raw_audio_path)
        
        # Remove silence and create optimized audio
        optimized_audio_path = await self.remove_silence_segments(
            raw_audio_path, silence_segments
        )
        
        return optimized_audio_path

    async def detect_silence(self, audio_path: Path) -> List[Tuple[float, float]]:
        """
        Detect silence segments in audio file.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            List of (start_time, end_time) tuples for silence segments
        """
        output_path = audio_path.parent / f"{audio_path.stem}_silence_detect.txt"
        
        cmd = [
            "ffmpeg",
            "-i", str(audio_path),
            "-af", f"silencedetect=noise={self.silence_threshold}:d={self.silence_duration}",
            "-f", "null",
            "-y",
            str(output_path)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                # Silence detection failed, return empty list (process full audio)
                return []
            
            # Parse silence detection output
            silence_segments = self._parse_silence_output(stderr.decode())
            return silence_segments
            
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found for silence detection")
    
    def _parse_silence_output(self, output: str) -> List[Tuple[float, float]]:
        """Parse FFmpeg silence detection output."""
        silence_segments = []
        lines = output.split('\n')
        
        silence_start = None
        for line in lines:
            if 'silence_start:' in line:
                try:
                    silence_start = float(line.split('silence_start: ')[1].split()[0])
                except (IndexError, ValueError):
                    continue
            elif 'silence_end:' in line and silence_start is not None:
                try:
                    silence_end = float(line.split('silence_end: ')[1].split()[0])
                    silence_segments.append((silence_start, silence_end))
                    silence_start = None
                except (IndexError, ValueError):
                    continue
        
        return silence_segments

    async def remove_silence_segments(
        self, 
        audio_path: Path, 
        silence_segments: List[Tuple[float, float]]
    ) -> Path:
        """
        Remove silence segments from audio file.
        
        Args:
            audio_path: Path to the input audio file
            silence_segments: List of silence segments to remove
            
        Returns:
            Path to the audio file with silence removed
        """
        if not silence_segments:
            # No silence detected, return original file
            return audio_path
        
        output_path = audio_path.parent / f"{audio_path.stem}_no_silence.wav"
        
        # Get total audio duration
        duration = await self._get_audio_duration(audio_path)
        
        # Create speech segments (inverse of silence segments)
        speech_segments = self._get_speech_segments(silence_segments, duration)
        
        if not speech_segments:
            # No speech detected, return original file
            return audio_path
        
        # Build FFmpeg filter for concatenating speech segments
        filter_parts = []
        input_parts = []
        
        for i, (start, end) in enumerate(speech_segments):
            # Add padding around speech segments
            padded_start = max(0, start - float(self.audio_padding))
            padded_end = min(duration, end + float(self.audio_padding))
            
            filter_parts.append(f"[0:a]atrim=start={padded_start}:end={padded_end},asetpts=PTS-STARTPTS[a{i}]")
            input_parts.append(f"[a{i}]")
        
        # Concatenate all speech segments
        concat_filter = "".join(filter_parts) + f"{''.join(input_parts)}concat=n={len(speech_segments)}:v=0:a=1[out]"
        
        cmd = [
            "ffmpeg",
            "-i", str(audio_path),
            "-filter_complex", concat_filter,
            "-map", "[out]",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            "-y",
            str(output_path)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                # Silence removal failed, return original file
                return audio_path
            
            return output_path
            
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found for silence removal")

    def _get_speech_segments(
        self, 
        silence_segments: List[Tuple[float, float]], 
        total_duration: float
    ) -> List[Tuple[float, float]]:
        """Convert silence segments to speech segments."""
        if not silence_segments:
            return [(0.0, total_duration)]
        
        speech_segments = []
        current_pos = 0.0
        
        for silence_start, silence_end in sorted(silence_segments):
            if current_pos < silence_start:
                speech_segments.append((current_pos, silence_start))
            current_pos = max(current_pos, silence_end)
        
        # Add final segment if there's speech after the last silence
        if current_pos < total_duration:
            speech_segments.append((current_pos, total_duration))
        
        return speech_segments

    async def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio file duration in seconds."""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(audio_path)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return float(stdout.decode().strip())
            else:
                return 0.0
                
        except (FileNotFoundError, ValueError):
            return 0.0

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
