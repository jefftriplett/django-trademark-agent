set dotenv-load := false

export JUST_UNSTABLE := "true"

@_default:
    just --list

@bootstrap *ARGS:
    pip install --upgrade pip uv

@demo:
    uv --quiet run django-trademark-agent.py "I'm working on an open source third party package, and I want to use django in the name of the package. Am I allowed to do that?"

@fmt:
    just --fmt

@lint *ARGS:
    just pre-commit {{ ARGS }} --all-files

@pre-commit *ARGS:
    uv --quiet tool run --with pre-commit-uv pre-commit run {{ ARGS }}
