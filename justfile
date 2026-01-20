set dotenv-load := false

export JUST_UNSTABLE := "true"

# List all available commands
@_default:
    just --list

# Process with the Django trademark agent
@agent *ARGS:
    uv --quiet run src/agent.py "{{ ARGS }}"

# Ask the trademark agent a question
@ask *ARGS:
    just agent "{{ ARGS }}"

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
