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
| `just web` | Launch the agent as a web chat interface |
| `just debug` | Print the compiled system prompt for debugging |
| `just demo` | Run a demo with a sample question |
| `just bootstrap` | Install pip and uv |
| `just fmt` | Format code |
| `just lint` | Run pre-commit hooks on all files |
| `just lint-autoupdate` | Update pre-commit hooks to latest versions |

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `PYDANTIC_AI_MODEL`: Model to use (default: `openai:gpt-5.4-nano`)

`PYDANTIC_AI_MODEL` is a [Pydantic AI model reference](https://ai.pydantic.dev/models/) in
`provider:model` form. The prefix is required — a bare model name raises `Unknown model` —
and it is what selects the provider:

| Prefix | API key | Notes |
|--------|---------|-------|
| `openai:` | `OPENAI_API_KEY` | The default (`openai:gpt-5.4-nano`) |
| `deepseek:` | `DEEPSEEK_API_KEY` | Works as-is |
| `openrouter:` | `OPENROUTER_API_KEY` | Works as-is |
| `together:` | `TOGETHER_API_KEY` | Works as-is |
| `ollama:` | `OLLAMA_API_KEY` | Works as-is; set `OLLAMA_BASE_URL` for a local server |
| `anthropic:` | `ANTHROPIC_API_KEY` | Needs the `anthropic` extra |
| `google:` | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Needs the `google` extra |
| `groq:` | `GROQ_API_KEY` | Needs the `groq` extra |
| `mistral:` | `MISTRAL_API_KEY` | Needs the `mistral` extra |
| `cohere:` | `CO_API_KEY` | Needs the `cohere` extra |
| `xai:` | `XAI_API_KEY` | Needs the `xai` extra |
| `bedrock:` | AWS credentials | Needs the `bedrock` extra |

```shell
export PYDANTIC_AI_MODEL=openai:gpt-5.4
export PYDANTIC_AI_MODEL=deepseek:deepseek-chat
```

"Works as-is" means the provider runs on the OpenAI SDK this agent already installs, so
only its API key is needed. The rest need their extra added to `pydantic-ai-slim[...]` in
the script header of `src/agent.py`. Either way `OPENAI_API_KEY` is read at import, so it
has to stay set even when another provider does the work.

## Requirements

- Python 3.12+
- OpenAI API key (set `OPENAI_API_KEY` environment variable)

## Installation

```shell
just bootstrap
```
