# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI科研助手** (AI Research Assistant) is a comprehensive system for automating experimental design, progress management, and result analysis using large language models (LLMs). The system supports multiple model providers (OpenAI, Gemini, Claude, iFlow) and integrates with RAGFlow for knowledge base retrieval.

### Key Features
- Intelligent experiment plan generation based on RAGFlow knowledge base
- Multi-model support with unified API variable system
- Template system with 9 built-in experiment types
- Progress tracking and status management
- Result analysis with data visualization and AI interpretation
- Web UI (Streamlit) and CLI interfaces
- HTTP proxy support for accessing restricted APIs
- Docker-based deployment with Redis and MongoDB

## Quick Start

### Docker Deployment (Recommended)
```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your API keys

# 2. Start services
docker-compose up -d

# 3. Access Web UI
# http://localhost:20339
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run Web UI
streamlit run ai_researcher/web_ui/main.py
```

## Common Commands

### Docker Operations
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f ai_researcher

# Restart service
docker-compose restart ai_researcher

# Stop services
docker-compose down

# View service status
docker-compose ps

# Test import in container
docker-compose exec ai_researcher python -c "from ai_researcher.config import save_config; print('✅ Import OK')"
```

### Testing
```bash
# Run all tests
python test_unified_api.py
python test_new_api.py
python test_proxy.py
python test_url_help.py
python test_ragflow_config.py
python test_ragflow_sdk.py
```

### CLI Usage
```bash
# Create experiment
ai-researcher create --model-provider openai --model-name gpt-4 "研究目标描述"

# List experiments
ai-researcher list
```

## Architecture

### Core Components

```
ai_researcher/
├── core/                      # Core coordination layer
│   ├── agent.py              # ResearchAgent - Main coordinator
│   ├── ragflow.py            # RAGFlow knowledge base integration
│   └── models/                # Model interfaces (OpenAI, Gemini, Claude, iFlow)
│
├── web_ui/                    # Streamlit-based Web UI
│   ├── main.py               # Entry point with navigation
│   ├── config.py             # Configuration management
│   ├── experiment_create.py  # Create experiments
│   └── result_analysis.py    # Analyze results
│
├── experiments/              # Experiment management
│   └── manager.py            # SQLite-based experiment tracking
│
├── templates/                # Experiment templates
│   └── manager.py            # Template system (9 built-in types)
│
├── results/                  # Result analysis
│   └── analyzer.py           # Data analysis and visualization
│
└── cli_tools/               # CLI integrations
    └── manager.py            # Unified CLI interface
```

### System Flow

```
User Input → RAGFlow Search → Template Loading → LLM Generation → Database Storage
                                              ↓
Progress Tracking ← Result Analysis ← Data Visualization
```

### Data Storage
- **SQLite**: Experiment data, progress tracking
- **MongoDB**: Document storage and metadata
- **Redis**: Caching layer
- **Local volumes**: Persistent data storage

### Key Integration Points

1. **ResearchAgent** (`ai_researcher/core/agent.py`)
   - Central coordinator for all operations
   - Handles experiment plan generation, progress updates, result analysis
   - Integrates with all other modules

2. **RAGFlow Integration** (`ai_researcher/core/ragflow.py`)
   - Recently updated to match official RAGFlow SDK
   - Supports semantic search, document management
   - Includes chat_completion() for OpenAI-compatible API

3. **Model System** (`ai_researcher/core/models/`)
   - Abstract factory pattern via BaseModel
   - Supports: OpenAI, Gemini, Claude, iFlow
   - Unified API through AI_API_KEY and AI_BASE_URL variables

4. **Configuration Management**
   - Environment variables for API keys
   - YAML files for system configuration
   - Web UI for in-app configuration (see config.py)

## Important Configuration

### Environment Variables
```bash
# Required
TOKEN=your_secure_password_here

# At least one model provider
OPENAI_API_KEY=...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
IFLOW_API_KEY=...

# Optional
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
NO_PROXY=localhost,127.0.0.1
```

### HTTP Proxy Support
The system supports HTTP/HTTPS proxies for accessing restricted APIs:
- Configure in `.env` file
- Can be enabled per-model in the Web UI configuration
- Supports authentication: `http://user:pass@proxy:port`

### NEW-API System
A unified API proxy that automatically selects the correct endpoint based on model name:
- Models with "gpt" or "openai" → `/v1/chat/completions`
- Models with "claude" or "anthropic" → `/v1/messages`
- Models with "gemini" or "google" → `/v1/generateContent`

## Key Files to Understand

1. **`ai_researcher/core/agent.py`**
   - Main ResearchAgent class
   - Coordinates all modules
   - Implements generate_experiment_plan(), update_progress(), analyze_results()

2. **`ai_researcher/web_ui/config.py`**
   - Configuration management UI
   - API key management (encrypted storage)
   - RAGFlow configuration
   - NEW-API settings

3. **`ai_researcher/models/config_manager.py`**
   - Model configuration database management
   - NEW-API proxy logic
   - Provider selection based on API format

4. **`ai_researcher/core/ragflow.py`**
   - Recently updated RAGFlow SDK implementation
   - Supports advanced search parameters
   - OpenAI-compatible chat_completion()
   - Full error handling with RAGFlowError

5. **`docker-compose.yml`**
   - Multi-service setup (ai_researcher, redis, mongodb)
   - Volume mounts for data persistence
   - Environment variable configuration

## Recent Major Updates

### 1. Unified API Variable System
Replaced provider-specific environment variables with AI_API_KEY and AI_BASE_URL abstraction layer that automatically maps to the correct SDK.

### 2. RAGFlow SDK Update
- Fixed API endpoints to match official RAGFlow SDK (plural endpoints)
- Added comprehensive error handling (RAGFlowError)
- Extended search() method with 13 parameters (document_ids, vector_similarity_weight, use_kg, etc.)
- Added OpenAI-compatible chat_completion() method

### 3. HTTP Proxy Support
- Added HTTP_PROXY, HTTPS_PROXY, NO_PROXY environment variables
- Can be enabled per-model in Web UI configuration
- Automatically passed to all SDK clients

### 4. URL Help Text System
- Enhanced API type selection with detailed help text
- Shows URL completion rules for each API type
- NEW-API path selection based on model name

## Testing Strategy

The project includes comprehensive test scripts:
- `test_unified_api.py` - Tests unified API system
- `test_new_api.py` - Tests NEW-API functionality
- `test_proxy.py` - Tests HTTP proxy integration
- `test_url_help.py` - Tests URL help text system
- `test_ragflow_config.py` - Tests RAGFlow configuration
- `test_ragflow_sdk.py` - Tests RAGFlow SDK integration

## Documentation Structure

Key documentation files:
- **`README.md`** - Project overview and quick start
- **`PROJECT_STRUCTURE.md`** - Detailed module structure
- **`SYSTEM_OVERVIEW.md`** - High-level architecture
- **`DOCKER_DEPLOYMENT.md`** - Docker deployment guide
- **`UNIFIED_API_SYSTEM.md`** - API abstraction layer design
- **`NEW_API_GUIDE.md`** - NEW-API proxy documentation
- **`HTTP_PROXY_GUIDE.md`** - Proxy configuration guide
- **`RAGFLOW_SDK_UPDATE.md`** - RAGFlow SDK update details
- **`MODEL_CONFIG.md`** - Model configuration guide

## Development Tips

### Adding New Model Provider
1. Create class in `ai_researcher/core/models/` inheriting from BaseModel
2. Implement all abstract methods
3. Register in `ResearchAgent._init_model()`

### Adding New Experiment Template
1. Edit `ai_researcher/templates/manager.py`
2. Add to `default_templates` dictionary
3. Or use Web UI template management page

### Web UI Development
- All pages in `ai_researcher/web_ui/`
- Main navigation in `main.py`
- Configuration management in `config.py`
- Use `st.session_state` for state management

### Database Operations
- SQLite for experiments: `/app/data/experiments/experiments.db`
- MongoDB for documents
- Model configs in model_configs table with encrypted API keys

### Error Handling
- RAGFlow operations raise RAGFlowError
- All modules include comprehensive logging
- Web UI shows user-friendly error messages

## Security Considerations

1. **API Keys**: Stored encrypted using TOKEN as password
2. **Configuration**: Use environment variables, never hardcode
3. **Docker**: Services run with appropriate permissions
4. **Proxy**: Proxy traffic may be monitored, use trusted proxies

## Performance Notes

1. **RAGFlow**: Add caching for repeated searches
2. **Database**: SQLite with indexes on frequently queried fields
3. **Batch Processing**: Supports bulk operations for efficiency
4. **Async Processing**: Consider async for long-running analyses

## Support and Resources

- **Web UI**: http://localhost:20339 (after docker-compose up)
- **RAGFlow**: Default port 9380 (if installed separately)
- **Redis**: localhost:6379
- **MongoDB**: localhost:27017
- **Logs**: `./logs/` directory (volume mounted)
- **Data**: `./data/` directory (volume mounted)
- **Backup**: `./backup/` directory (volume mounted)

## Recent Technical Decisions

1. **API Format Classification**: Use API format (chat, messages, generateContent) instead of provider names for flexibility
2. **NEW-API Proxy**: Single endpoint supporting multiple formats via model name detection
3. **Embedded Configuration**: Web UI configuration replaces environment variables for many settings
4. **Plural Endpoints**: RAGFlow SDK updated to use plural API endpoints (/datasets, not /dataset)
5. **PYTHONPATH Configuration**: Added PYTHONPATH=/app:/app/ai_researcher to docker-compose.yml and Dockerfile to fix import issues in containers

## Troubleshooting

### Import Errors

**Error**: `cannot import name 'save_config' from 'ai_researcher.config'`

**Solution**: Ensure PYTHONPATH is set correctly in Docker container:
- Check `docker-compose.yml` has `PYTHONPATH=/app:/app/ai_researcher` in environment
- Restart services: `docker-compose restart ai_researcher`
- Verify: `docker-compose exec ai_researcher python -c "from ai_researcher.config import save_config"`

### Docker Container Issues

**Code not updating**: Volume mount might be stale
- Solution: `docker-compose restart ai_researcher`

**Import fails**: PYTHONPATH not set
- Solution: Check environment variables in docker-compose.yml

### RAGFlow Connection Issues

**Connection refused**: RAGFlow service not running
- Start RAGFlow: `ragflowd` or `docker run -d -p 9380:9380 ragflow/ragflow:latest`
- Configure endpoint in Web UI: Configuration Management → RAGFlow Knowledge Base Configuration
