# Django Trademark Agent (Unofficial)

An AI agent that helps answer common questions about Django's Trademark policy.

**DISCLAIMER:** This is not official or legal advice. This tool is intended for educational purposes only.

## Usage

```shell
# Ask about trademark policy
just ask "Can I use 'django' in my company name?"

# Or use uv directly
uv run src/agent.py ask "Can I use 'django' in my company name?"
```

## Available Commands

| Command | Description |
|---------|-------------|
| `just` | List all available commands |
| `just ask "..."` | Ask the trademark agent a question |
| `just debug` | Print the compiled system prompt for debugging |
| `just demo` | Run a demo with a sample question |
| `just bootstrap` | Install pip and uv |
| `just fmt` | Format code |
| `just lint` | Run pre-commit hooks on all files |
| `just lint-autoupdate` | Update pre-commit hooks to latest versions |

## Requirements

- Python 3.12+
- OpenAI API key (set `OPENAI_API_KEY` environment variable)

## Installation

```shell
just bootstrap
```
