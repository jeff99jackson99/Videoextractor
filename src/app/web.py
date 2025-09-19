"""FastAPI web application for video processing and transcription."""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any

import aiofiles
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .services.video_processor import VideoProcessor
from .services.transcription import TranscriptionService
from .services.summarization import SummarizationService

app = FastAPI(
    title="Video Extractor API",
    description="Extract audio, generate transcripts and summaries from videos",
    version="0.1.0"
)

# Initialize services
video_processor = VideoProcessor()
transcription_service = TranscriptionService()
summarization_service = SummarizationService()


class ProcessingResult(BaseModel):
    """Result of video processing."""
    transcript: str
    summary: str
    processing_time: float
    video_duration: float


@app.get("/healthz")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "video-extractor"}


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with API information."""
    return {
        "message": "Video Extractor API",
        "version": "0.1.0",
        "endpoints": {
            "health": "/healthz",
            "upload": "/upload-video",
            "process": "/process-video"
        }
    }


@app.post("/upload-video", response_model=ProcessingResult)
async def upload_and_process_video(
    file: UploadFile = File(...)
) -> ProcessingResult:
    """
    Upload a video file and process it to extract transcript and summary.
    
    Args:
        file: Uploaded video file
        
    Returns:
        ProcessingResult with transcript, summary, and metadata
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(
            status_code=400,
            detail="File must be a video format"
        )
    
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Save uploaded file
        video_path = temp_path / f"input_{file.filename}"
        async with aiofiles.open(video_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        try:
            # Extract audio from video
            audio_path = await video_processor.extract_audio(video_path)
            
            # Get video metadata
            video_info = await video_processor.get_video_info(video_path)
            
            # Transcribe audio
            transcript = await transcription_service.transcribe_audio(audio_path)
            
            # Generate summary
            summary = await summarization_service.generate_summary(transcript)
            
            return ProcessingResult(
                transcript=transcript,
                summary=summary,
                processing_time=0.0,  # TODO: Add timing
                video_duration=video_info.get("duration", 0.0)
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing video: {str(e)}"
            )


@app.post("/process-video")
async def process_existing_video(video_path: str) -> ProcessingResult:
    """
    Process an existing video file by path.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        ProcessingResult with transcript, summary, and metadata
    """
    video_file = Path(video_path)
    
    if not video_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Video file not found: {video_path}"
        )
    
    try:
        # Extract audio from video
        audio_path = await video_processor.extract_audio(video_file)
        
        # Get video metadata
        video_info = await video_processor.get_video_info(video_file)
        
        # Transcribe audio
        transcript = await transcription_service.transcribe_audio(audio_path)
        
        # Generate summary
        summary = await summarization_service.generate_summary(transcript)
        
        return ProcessingResult(
            transcript=transcript,
            summary=summary,
            processing_time=0.0,  # TODO: Add timing
            video_duration=video_info.get("duration", 0.0)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing video: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
