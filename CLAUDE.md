# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

This project uses **pipenv** for Python environment management. Run commands directly with `python script.py` as the environment is assumed to be active.

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

**Provider Abstraction**: Single interface supports both OpenAI and Anthropic models with automatic provider selection

**Tool System**: Decorative approach using docstrings for automatic schema generation rather than manual tool definitions

**Streaming Architecture**: Real-time response streaming with callback handlers for different interfaces

**Story Persistence**: File-based story management with automatic state saving/loading

## File Structure Context

- `stories/`: Individual story directories with game state
- `app/`: Web interface assets (templates, static files)
- Root Python files: Core application logic and abstractions