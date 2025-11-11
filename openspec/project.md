# Project Context

## Purpose
MetaGPT is a multi-agent framework that enables AI agents to collaborate as a software development team. It takes a one-line requirement as input and outputs comprehensive software development artifacts including user stories, competitive analysis, requirements, data structures, APIs, and documents. The system simulates a complete software company with different roles (Product Manager, Architect, Project Manager, Engineer) working together following carefully orchestrated Standard Operating Procedures (SOPs).

The core philosophy is `Code = SOP(Team)` - materializing software development processes and applying them to teams composed of LLMs.

## Tech Stack
- **Core Language**: Python 3.9-3.11
- **Main Dependencies**:
  - `aiohttp` - Async HTTP client/server
  - `pydantic` - Data validation and settings management (>=2.5.3)
  - `openai` - OpenAI API client (~1.64.0)
  - `anthropic` - Anthropic API client (0.47.2)
  - `fire` - Command-line interface framework
  - `typer` - Modern CLI framework (0.9.0)
  - `loguru` - Logging library (0.6.0)
  - `PyYAML` - YAML parser (6.0.1)
  - `tiktoken` - OpenAI tokenizer (0.7.0)
- **Vector Databases**:
  - `faiss_cpu` (1.7.4), `qdrant-client` (1.7.0), `lancedb` (0.4.0), `chromadb`, `milvus`
- **Web/Network**:
  - `playwright` for web scraping, `beautifulsoup4` (4.12.3), `selenium`
- **Data Processing**:
  - `pandas` (2.1.1), `numpy` (~1.26.4), `openpyxl` (~3.1.5)
- **Development Tools**:
  - `black` (~23.3.0), `isort` (~5.12.0), `pylint` (~3.0.3), `pre-commit` (~3.6.0)

## Project Conventions

### Code Style
- **Formatter**: Black with line length 120
- **Import Sorting**: isort with black profile
- **Linting**: Ruff and pylint
- **Pre-commit hooks**: Configured with isort, ruff, and black
- **Naming**: Python PEP 8 conventions
- **File Structure**: Modular organization under `metagpt/` package

### Architecture Patterns
- **Multi-Agent System**: Role-based architecture with specialized agents
- **Async Programming**: Extensive use of asyncio for concurrent operations
- **Action-Node Pattern**: Hierarchical action system with `ActionNode` base class
- **Environment Context**: Centralized context management through `Context` class
- **Configuration Management**: YAML-based configuration with role-specific settings
- **Document Processing**: Unified document handling with markdown focus
- **LLM Abstraction**: Provider-agnostic LLM interface supporting multiple providers

### Testing Strategy
- **Framework**: pytest with asyncio support
- **Test Structure**: Comprehensive test suite under `tests/` directory
- **Mocking**: Extensive mock infrastructure for LLM calls and HTTP requests
- **Test Categories**: Unit tests, integration tests, end-to-end tests
- **Coverage**: pytest-cov for coverage reporting
- **Fixtures**: Rich fixture system for test isolation and setup

### Git Workflow
- **Branching**: Main branch for stable releases
- **Merge Strategy**: Pull request-based merges
- **Commit Style**: Conventional commits with clear descriptions
- **Pre-commit**: Automated formatting and linting on commit
- **Release Flow**: Versioned releases through setup.py

## Domain Context
- **Multi-Agent Collaboration**: Agents simulate different software development roles
- **SOP-Driven Development**: Standard Operating Procedures guide agent behavior
- **LLM-Powered**: Core functionality relies on Large Language Models
- **Document Generation**: Automatic generation of software artifacts
- **Code Generation**: AI-assisted code writing and review
- **Research Integration**: Built-in capabilities for research and analysis

## Important Constraints
- **Python Version**: Requires Python 3.9+ but <3.12
- **External Dependencies**: Requires API keys for LLM providers (OpenAI, Anthropic, etc.)
- **Node.js Required**: For certain tools (Mermaid CLI, web scraping)
- **Memory Usage**: LLM interactions can be memory-intensive
- **Network Dependencies**: Requires internet access for LLM API calls and search
- **Configuration**: Proper YAML configuration required for different LLM providers

## External Dependencies
- **LLM Providers**: OpenAI, Anthropic, Azure OpenAI, Google, various Chinese providers
- **Vector Stores**: Optional external vector databases (Qdrant, Milvus, etc.)
- **Search APIs**: Google Search API, DuckDuckGo, SerpAPI
- **Cloud Storage**: AWS S3 (optional)
- **Document Processing**: External OCR and parsing services
- **Web Services**: Various APIs for web scraping and data retrieval
