.PHONY: help setup dev test lint fmt docker/build docker/run clean install

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Set up development environment
	pip install -e ".[dev]"
	pre-commit install

install: ## Install dependencies only
	pip install -e .

dev: ## Run development servers (FastAPI + Streamlit)
	@echo "Starting FastAPI server in background..."
	@python -m src.app &
	@echo "FastAPI PID: $$!" > .api.pid
	@sleep 3
	@echo "Starting Streamlit app..."
	@streamlit run streamlit_app.py --server.port 8501
	@echo "Stopping FastAPI server..."
	@kill `cat .api.pid` 2>/dev/null || true
	@rm -f .api.pid

dev-api: ## Run only FastAPI server
	python -m src.app

dev-streamlit: ## Run only Streamlit app
	streamlit run streamlit_app.py

test: ## Run tests
	pytest tests/ -v

lint: ## Run linting
	ruff check src/ tests/ streamlit_app.py
	mypy src/ streamlit_app.py

fmt: ## Format code
	black src/ tests/ streamlit_app.py
	ruff --fix src/ tests/ streamlit_app.py

docker/build: ## Build Docker image
	docker build -t video-extractor:latest .

docker/run: ## Run Docker container
	docker run -p 8000:8000 -p 8501:8501 --env-file .env video-extractor:latest

docker/dev: ## Run with docker-compose for development
	docker-compose up --build

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -f .api.pid

check-ffmpeg: ## Check if ffmpeg is installed
	@which ffmpeg > /dev/null || (echo "❌ FFmpeg not found. Install with: brew install ffmpeg" && exit 1)
	@echo "✅ FFmpeg is installed"

check-env: ## Check environment variables
	@test -f .env || (echo "❌ .env file not found. Copy .env.example to .env and configure." && exit 1)
	@echo "✅ Environment file found"

validate: check-ffmpeg check-env ## Validate environment setup
	@echo "✅ Environment validation complete"
