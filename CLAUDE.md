# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

This project uses **uv** for Python dependency management with **pipenv** compatibility. The environment should be activated before running any commands. Run commands directly with `python script.py` as the environment is assumed to be active.

### Common Development Commands

- **Install dependencies**: `uv sync` or `pipenv install`
- **Add new dependency**: `uv add <package>` or edit `pyproject.toml`
- **Run tests**: No testing framework currently configured
- **Lint code**: No linting configured - consider adding ruff or flake8 if code quality checks are needed

## Running the Application

- **Web interface**: `python app.py` (runs Flask-SocketIO server on port 5001)
- **Terminal interface**: `python terminal.py` (interactive CLI version)

## Architecture Overview

This is a Harry Potter-themed RPG application with both web and terminal interfaces that integrates AI assistants for interactive storytelling.

### Core Components

**API Layer (`api.py`)**:
- Defines `Assistant` abstract base class and concrete implementations (`OpenAIAssistant`, `AnthropicAssistant`)
- Handles model selection, conversation history, tool execution, and streaming responses
- Factory function `makeAssistant()` automatically selects provider based on model name patterns

**Tool System (`model_tools.py`)**:
- Dynamic tool registration using docstring parsing for schema generation
- `Toolbox` class manages collections of tools with default kwargs
- Story-specific tools for file I/O, dice rolling, and game mechanics
- Auto-generates OpenAI and Anthropic-compatible schemas
- Tool handlers use docstring format: `tool_name: description` on first line, then `param_name(type): description` for each parameter

**Web Application (`app.py`)**:
- Flask-SocketIO server with real-time communication
- Story selection and creation interface
- Uses `WebCallbackHandler` for streaming responses to browser
- Manages assistant instances per story with persistent history

**Callback System (`callbacks.py`)**:
- `CallbackHandler` interface for different output modes
- `TerminalPrinter` for CLI colored output
- `WebCallbackHandler` for real-time web updates via SocketIO

### Game System Integration

**Instructions and Ruleset**:
- `instructions.md`: Complete Harry Potter RPG ruleset with D&D-inspired mechanics
- `planning_guide.md`: AI storytelling guidelines for narrative consistency
- Stories stored in `./stories/{story_name}/` with character sheets, plans, and history

**Story Management**:
- Each story has its own directory with markdown files
- `history.json` stores conversation state
- Tools provide file I/O within story directories
- Automatic story summarization and planning capabilities

### Frontend (Web Interface)

- Real-time chat interface with SocketIO
- Story selection sidebar
- Markdown rendering with special `<narration>` tags
- Conversation export functionality
- Discord-inspired dark theme

## Key Design Patterns

**Provider Abstraction**: Single interface supports both OpenAI and Anthropic models with automatic provider selection based on model name patterns (e.g., "claude-" prefix selects Anthropic, "gpt-" selects OpenAI)

**Tool System**: Declarative approach using docstrings for automatic schema generation rather than manual tool definitions - eliminates code duplication between OpenAI and Anthropic tool schemas

**Streaming Architecture**: Real-time response streaming with callback handlers for different interfaces (`TerminalPrinter` for CLI, `WebCallbackHandler` for web)

**Story Persistence**: File-based story management with automatic state saving/loading - each story gets its own directory with character sheets, history, and planning documents

**Callback Pattern**: Abstract `CallbackHandler` interface allows the same assistant logic to work with different output modes (terminal vs web)

## File Structure Context

- `stories/`: Individual story directories with game state - not tracked in git
- `app/`: Web interface assets (templates, static files)  
- `instructions.md`: Complete Harry Potter RPG ruleset (35KB+ comprehensive game mechanics)
- `planning_guide.md`: AI storytelling guidelines for narrative consistency
- Root Python files: Core application logic and abstractions

## Model Configuration

The `makeAssistant()` factory function in `api.py` automatically selects between OpenAI and Anthropic based on model name patterns:
- Models starting with "claude-" use `AnthropicAssistant`
- Models starting with "gpt-" use `OpenAIAssistant`  
- Default models are currently set to `claude-sonnet-4-20250514` in `app.py`

## Tool Development Guidelines

When adding new tools to `model_tools.py`:
1. Use docstring format: `tool_name: description` on first line
2. Document parameters as `param_name(type): description` 
3. The `Toolbox` class will auto-generate both OpenAI and Anthropic schemas
4. Use `default_kwargs` for context like `current_story` that all tools need

## Story Management Architecture

Each story requires three core files to function:
- `pc.md`: Player character sheet
- `story_plan.md`: Complete narrative structure (private to AI)
- `story_summary.md`: Running story summary for continuity

The application enforces this structure and guides users through creation if files are missing.