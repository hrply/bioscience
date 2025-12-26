# 生物科学文献阅读助手 - Qwen Code Context

## 项目概述

This is a bioinformatics literature reading assistant system built with Python and Streamlit, designed to help researchers efficiently read, analyze, and organize scientific literature. The project leverages AI technology to provide literature summary generation, key information extraction, literature classification, and intelligent search capabilities.

The system integrates with RAGFlow for document processing and supports multiple large language models (OpenAI, Qwen, Claude, local models via Ollama).

## Key Features

- **📚 Literature Library Management**: Connect to RAGFlow to manage literature collections
- **🔍 Intelligent Search**: Semantic-based literature search and retrieval  
- **⛏️ Deep Mining**: AI-driven literature analysis and insights
- **📊 Trend Analysis**: Research trend identification and knowledge graph construction
- **💡 Smart Recommendations**: Research suggestions based on analysis results
- **🌐 Research Network**: Author collaboration, institution relations, topic networks
- **🔄 Concept Evolution**: Historical development trajectory analysis of key concepts
- **📝 Interactive Reading**: Annotation, notes, and highlighting features

## Technical Stack

- **Frontend**: Streamlit 1.28+
- **Backend**: Python 3.8+
- **Database**: SQLite + ChromaDB (vector database)
- **AI Models**: Multiple providers supported (OpenAI, Qwen, Claude, local Ollama)
- **Document Processing**: PyMuPDF, pdfplumber, BeautifulSoup
- **Text Analysis**: NLTK, spaCy, scikit-learn, transformers
- **Deployment**: Docker, Docker Compose

## Project Structure

```
bioscience/research/readhelper/
├── main.py                    # Simplified main entry point
├── requirements.txt           # Core dependencies
├── docker-compose.yml         # Docker deployment configuration
├── docker-start.sh            # Docker startup script
├── Makefile                   # Build and deployment commands
├── IFLOW.md                   # Detailed documentation
├── README.md                  # Project overview
├── .env.example              # Environment variables template
├── src/                      # Main source directory
│   ├── main.py              # Complete main entry point  
│   ├── start.sh             # Quick startup script
│   ├── config/              # Configuration module
│   │   ├── settings.py      # Application configuration
│   │   └── prompts.py       # AI prompt templates
│   ├── core/                # Core modules
│   │   ├── ragflow_client.py    # RAGFlow client
│   │   ├── llm_client.py        # Large language model client
│   │   ├── literature_miner.py  # Literature mining engine
│   │   └── document_processor.py # Document processor
│   ├── interfaces/          # Interface layer
│   │   └── streamlit_ui/    # Streamlit interface pages
│   │       ├── home.py      # Home page
│   │       ├── library_tab.py   # Library page
│   │       ├── mining_tab.py    # Mining page
│   │       ├── search_tab.py    # Search page
│   │       └── config_tab.py    # Configuration page
│   ├── services/            # Service layer
│   ├── storage/             # Storage layer
│   ├── utils/               # Utility classes
│   └── tests/               # Test modules
```

## Building and Running

### Method 1: Docker Deployment (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd bioscience/research/readhelper

# Start services (one-click)
./docker-start.sh

# Or using Docker Compose directly
docker-compose up -d

# Access the application
# Literature Miner: http://localhost:8501
# RAGFlow Admin: http://localhost:9380
```

### Method 2: Local Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env file, fill in your API keys

# Start the application
cd src
chmod +x start.sh
./start.sh
```

### Using Makefile Commands

```bash
# View all available commands
make help

# Start services
make up

# View service status
make status

# View application logs
make logs

# Enter container
make shell

# Stop services
make down

# Clean resources
make clean
```

## Configuration

### Environment Variables

Key configuration in `.env` file:

```env
# RAGFlow Configuration
RAGFLOW_API_KEY=your_ragflow_api_key
RAGFLOW_BASE_URL=http://localhost:9380

# LLM Provider Configuration
LLM_PROVIDER=qwen      # qwen, openai, claude, local
LLM_API_KEY=your_api_key
LLM_MODEL=qwen-turbo   # Model name depends on provider
LLM_BASE_URL=http://localhost:11434  # For local models
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
```

### Supported LLM Providers

1. **Qwen (Recommended)**
```env
LLM_PROVIDER=qwen
LLM_API_KEY=your_qwen_api_key
LLM_MODEL=qwen-turbo
```

2. **OpenAI**
```env
LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key
LLM_MODEL=gpt-3.5-turbo
```

3. **Claude**
```env
LLM_PROVIDER=claude
LLM_API_KEY=your_anthropic_api_key
LLM_MODEL=claude-3-sonnet-20240229
```

4. **Local (Ollama)**
```env
LLM_PROVIDER=local
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=llama2
```

## Development Guidelines

### Adding New Features

1. **Core Functions**: Add new modules in `src/core/` directory
2. **User Interface**: Add new pages in `src/interfaces/streamlit_ui/` directory
3. **Configuration**: Add new configuration items in `src/config/settings.py`

### Custom Prompts

Edit `src/config/prompts.py` file to modify AI analysis prompt templates.

### Extending LLM Support

Add new client class in `src/core/llm_client.py` and register in factory class.

## Dependencies

Key dependencies are defined in `requirements.txt`:
- Streamlit for the web interface
- PyMuPDF for PDF processing
- Requests for HTTP clients
- Transformers and PyTorch for NLP
- ChromaDB for vector storage
- Various libraries for text processing, visualization, and AI

## Troubleshooting

### Common Issues

1. **RAGFlow Connection Failure**
   - Check if RAGFlow service is running normally
   - Confirm API key is correct
   - Verify network connectivity

2. **Large Model API Call Failure**
   - Check if API key is valid
   - Confirm network connectivity is normal
   - Verify model name is correct

3. **Literature mining results inaccurate**
   - Adjust similarity threshold
   - Increase document count
   - Optimize research topic description

4. **Application startup failure**
   - Check if Python version meets requirements
   - Confirm all dependencies are installed
   - Check error logs

### Log Locations

Application logs: `~/.literature_helper/logs/app.log`

## Performance Optimization

### Speed Up Analysis

1. **Reduce Document Count**: Lower max documents during mining
2. **Adjust Similarity Threshold**: Increase threshold to reduce processed docs
3. **Use More Powerful Hardware**: Increase CPU and memory resources

### Reduce API Costs

1. **Choose Appropriate Model**: Select different cost models based on needs
2. **Optimize Prompts**: Reduce unnecessary API calls
3. **Enable Caching**: Use cached results for repeated queries