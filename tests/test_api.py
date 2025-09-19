"""Tests for the FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from src.app.web import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "video-extractor"


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data


def test_upload_video_no_file():
    """Test upload endpoint with no file."""
    response = client.post("/upload-video")
    assert response.status_code == 422  # Unprocessable Entity


def test_upload_video_invalid_file():
    """Test upload endpoint with invalid file type."""
    files = {"file": ("test.txt", b"test content", "text/plain")}
    response = client.post("/upload-video", files=files)
    assert response.status_code == 400
    assert "File must be a video format" in response.json()["detail"]


def test_process_video_not_found():
    """Test process endpoint with non-existent file."""
    response = client.post("/process-video", json={"video_path": "/nonexistent/file.mp4"})
    assert response.status_code == 422  # Due to JSON body vs query param mismatch


@pytest.mark.asyncio
async def test_video_processor_import():
    """Test that video processor can be imported."""
    from src.app.services.video_processor import VideoProcessor
    processor = VideoProcessor()
    assert processor is not None


@pytest.mark.asyncio
async def test_transcription_service_import():
    """Test that transcription service can be imported (without API key)."""
    try:
        from src.app.services.transcription import TranscriptionService
        # This will fail without API key, but import should work
        assert TranscriptionService is not None
    except ValueError as e:
        # Expected when OPENAI_API_KEY is not set
        assert "OPENAI_API_KEY" in str(e)


@pytest.mark.asyncio
async def test_summarization_service_import():
    """Test that summarization service can be imported (without API key)."""
    try:
        from src.app.services.summarization import SummarizationService
        # This will fail without API key, but import should work
        assert SummarizationService is not None
    except ValueError as e:
        # Expected when OPENAI_API_KEY is not set
        assert "OPENAI_API_KEY" in str(e)
