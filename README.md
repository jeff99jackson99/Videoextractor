# 🎥 Video Extractor

A powerful video processing application that extracts audio, generates transcripts, and creates AI-powered summaries from video files. Built with FastAPI backend and Streamlit frontend.

## ✨ Features

- 🎵 **Audio Extraction**: Extract high-quality audio from video files using FFmpeg
- 🔇 **Smart Silence Removal**: Automatically detect and remove silence to reduce processing time and costs
- 📝 **Speech-to-Text**: Generate accurate transcripts using OpenAI Whisper
- 🤖 **AI Summarization**: Create intelligent summaries using GPT models
- 📊 **Processing Efficiency**: Real-time statistics showing silence removal and time savings
- 🌐 **Web Interface**: User-friendly Streamlit frontend for easy video upload
- 🚀 **REST API**: FastAPI backend for programmatic access
- 📁 **Large File Support**: Handle video files up to 2GB
- 🐳 **Docker Support**: Containerized deployment with multi-stage builds
- 🔄 **CI/CD Pipeline**: Automated testing and releases via GitHub Actions

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- FFmpeg (for video/audio processing)
- OpenAI API Key

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/jeff99jackson99/Videoextractor.git
   cd Videoextractor
   ```

2. **Set up environment**:
   ```bash
   make setup
   ```

3. **Configure environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your OpenAI API key
   ```

4. **Install FFmpeg** (if not already installed):
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   ```

### Running the Application

#### Option 1: Development Mode (Recommended)
```bash
make dev
```
This starts both FastAPI (port 8000) and Streamlit (port 8501) servers.

#### Option 2: Individual Services
```bash
# FastAPI only
make dev-api

# Streamlit only
make dev-streamlit
```

#### Option 3: Docker
```bash
make docker/build
make docker/run
```

## 🎯 Usage

### Web Interface (Streamlit)

1. Open http://localhost:8501 in your browser
2. Upload a video file (MP4, MOV, AVI, etc.)
3. Click "Process Video" and wait for completion
4. Download transcript and summary files

### REST API

#### Upload and Process Video
```bash
curl -X POST "http://localhost:8000/upload-video" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your-video.mp4"
```

#### Health Check
```bash
curl http://localhost:8000/healthz
```

## 🛠️ Development

### Available Commands

```bash
make help          # Show all available commands
make setup         # Set up development environment
make dev           # Run development servers
make test          # Run tests
make lint          # Run linting
make fmt           # Format code
make docker/build  # Build Docker image
make validate      # Validate environment setup
```

### Project Structure

```
video-extractor/
├── src/app/                 # FastAPI application
│   ├── services/           # Business logic services
│   ├── web.py             # FastAPI routes
│   └── __main__.py        # Application entry point
├── streamlit_app.py        # Streamlit frontend
├── tests/                  # Test suite
├── .github/workflows/      # CI/CD pipelines
├── Dockerfile             # Container definition
├── docker-compose.yml     # Docker Compose config
├── Makefile              # Development commands
└── pyproject.toml        # Project configuration
```

### Testing

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Quality

```bash
# Lint code
make lint

# Format code
make fmt

# Type checking
mypy src/ streamlit_app.py
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Build image
docker build -t video-extractor .

# Run container
docker run -p 8000:8000 -p 8501:8501 \
  -e OPENAI_API_KEY=your_key_here \
  video-extractor
```

### Docker Compose

```bash
# Development
docker-compose up --build

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## 📋 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-3.5-turbo` |
| `API_BASE_URL` | FastAPI base URL | `http://localhost:8000` |
| `DEBUG` | Enable debug mode | `true` |
| `LOG_LEVEL` | Logging level | `info` |
| `MAX_FILE_SIZE_MB` | Max upload size (MB) | `2000` |
| `SILENCE_THRESHOLD` | Silence detection threshold | `-30dB` |
| `SILENCE_DURATION` | Min silence duration to detect | `0.5` |
| `AUDIO_PADDING` | Padding around speech segments | `0.2` |

## 🚀 Deployment

### GitHub Actions

The project includes automated CI/CD pipelines:

- **CI Pipeline**: Runs tests, linting, and builds on every push
- **Release Pipeline**: Builds and publishes Docker images on tag creation

### Creating a Release

```bash
git tag v1.0.0
git push origin v1.0.0
```

This triggers the release pipeline and publishes the Docker image to GitHub Container Registry.

## 📚 API Documentation

Once the FastAPI server is running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`make test lint`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework for APIs
- [Streamlit](https://streamlit.io/) - Rapid web app development
- [OpenAI Whisper](https://openai.com/research/whisper) - Speech recognition
- [FFmpeg](https://ffmpeg.org/) - Multimedia processing

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/jeff99jackson99/Videoextractor/issues) page
2. Create a new issue with detailed information
3. Join the discussion in [Discussions](https://github.com/jeff99jackson99/Videoextractor/discussions)

---

Built with ❤️ using Python, FastAPI, and Streamlit
