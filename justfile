set dotenv-load := false

export JUST_UNSTABLE := "true"

# List all available commands
@_default:
    just --list

# Ask the bylaws agent a question
@ask *ARGS:
    uv --quiet run agent.py "{{ ARGS }}"

# Install pip and uv package management tools
@bootstrap *ARGS:
    pip install --upgrade pip uv

# Run a demo with a sample question
@demo:
    just ask "I'm working on an open source third party package, and I want to use django in the name of the package. Am I allowed to do that?"

# Format code using just's built-in formatter
@fmt:
    just --fmt

# Run pre-commit checks on files
@lint *ARGS="--all-files":
    uv --quiet tool run --with pre-commit-uv pre-commit run {{ ARGS }}
