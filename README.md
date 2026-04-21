# Multi-Model AI Chatbot System

A modular Python-based AI agent system that integrates OpenAI, Anthropic, Google Gemini, and DeepSeek.

## Features
- **Intelligent Routing**: Automatically selects the best model (Coding -> DeepSeek, Reasoning -> Claude, Fast -> Gemini).
- **Ensemble Mode**: Queries multiple models and uses a judge (GPT-4o) to rank and select the best response.
- **Reflection Loop**: Self-critique mechanism (Generate -> Critique -> Improve).
- **Memory**: Maintains conversation history.
- **Cost Tracking**: Tracks usage costs per model in real-time.
- **Rich CLI**: Beautiful terminal interface using `rich`.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```

3. **Run the Chatbot**:
   ```bash
   python -m app.main
   ```

## CLI Commands
- `/model <model_id>`: Switch to a specific model (e.g., `gpt-4o`, `claude-3-5-sonnet`, `gemini-1.5-flash`, `deepseek-chat`).
- `/mode <mode>`: Switch mode (`auto`, `ensemble`, `reflection`).
- `/clear`: Clear conversation memory.
- `/cost`: View total session cost and breakdown.
- `/exit`: Quit the application.

## Project Structure
- `app/models/`: Wrapper classes for different AI providers.
- `app/agents/`: Routing and orchestration logic.
- `app/memory/`: Conversation history management.
- `app/utils/`: Logging, cost tracking, and prompt building.
- `app/config.py`: Central configuration and pricing.
