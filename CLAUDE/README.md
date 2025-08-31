# CLAUDE Development Setup

This guide will help you set up the CLAUDE development environment.

## Prerequisites

### System Requirements
- macOS 14.0 or later
- Python 3.10 or later
- Xcode 15.0 or later (for SwiftUI frontend)
- Ollama installed locally (for LLM functionality)

### Install Dependencies

1. **Install Ollama**
   ```bash
   brew install ollama
   ollama pull codellama:7b
   ```

2. **Install Python Dependencies**
   ```bash
   cd CLAUDE/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

## Running the Application

### Backend Server
```bash
cd CLAUDE/backend
source venv/bin/activate
python main.py
```

The backend API will be available at `http://localhost:8000`

### Frontend Application
```bash
cd CLAUDE/frontend
open CLAUDE.xcodeproj
```

Build and run the application in Xcode.

## API Documentation

The backend provides REST API endpoints at `http://localhost:8000`:

### Core Endpoints
- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /query` - Execute RAG query
- `POST /generate-code` - Generate code with context

### Indexing Endpoints
- `POST /index/directory` - Index a directory
- `GET /index/stats` - Get indexing statistics

### Style Analysis
- `POST /style/analyze` - Analyze code style
- `GET /style/guidelines` - Get style guidelines

### Monitoring
- `GET /monitoring/status` - Get monitoring status
- `POST /monitoring/start` - Start monitoring
- `POST /monitoring/stop` - Stop monitoring

### System Management
- `GET /system/status` - Get system status
- `POST /llm/check-availability` - Check LLM availability
- `POST /llm/pull-model` - Pull LLM model

## Configuration

### Backend Configuration (.env)
```
LLM_MODEL=codellama:7b
OLLAMA_BASE_URL=http://localhost:11434
VECTOR_DB_PATH=./data/vector_db
STORAGE_TYPE=local
API_HOST=127.0.0.1
API_PORT=8000
ENABLE_FILE_WATCHER=true
```

### Frontend Configuration
The frontend is configured in `APIService.swift`:
- API base URL: `http://localhost:8000`
- Default settings in Settings view

## Development Workflow

1. **Start Backend Server**
   ```bash
   cd backend
   python main.py
   ```

2. **Start Frontend**
   - Open `CLAUDE.xcodeproj` in Xcode
   - Build and run the application

3. **Test Functionality**
   - Select a codebase directory
   - Enter coding queries
   - Verify context-aware responses

## Troubleshooting

### Common Issues

1. **Ollama Not Running**
   ```bash
   ollama serve
   ```

2. **Model Not Available**
   ```bash
   ollama pull codellama:7b
   ```

3. **Port Already in Use**
   - Change `API_PORT` in `.env`
   - Or kill the process using the port

4. **Dependencies Missing**
   ```bash
   pip install -r requirements.txt
   ```

### Logs
- Backend logs: Check console output or log file
- Frontend logs: Use Xcode console

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.