#!/usr/bin/env -S uv --quiet run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx",
#     "environs",
#     "pydantic-ai-slim[openai]",
#     "pydantic-ai-slim[web]",
#     "rich",
#     "typer",
#     "uvicorn",
# ]
# ///

import httpx
import typer
import uvicorn

from environs import env
from pathlib import Path
from pydantic import BaseModel
from pydantic import Field
from pydantic_ai import Agent
from rich.console import Console

console = Console()

OPENAI_API_KEY: str = env.str("OPENAI_API_KEY")
OPENAI_MODEL_NAME: str = env.str("OPENAI_MODEL_NAME", default="gpt-5-mini")

SYSTEM_PROMPT = """
<system_context>

You are a Trademark policy assistant for the Django Software Foundation.

</system_context>

<behavior_guidelines>

- Please answer all questions using Django's trademark policy and frequently asked questions.

- Please warn the user that this not official or legal advice.

</behavior_guidelines>
"""


class Output(BaseModel):
    approved: bool
    answer: str = Field(description="The answer to our question")
    reasoning: str = Field(description="The reasoning and support for our answer based on our source material")
    sections: list[str] = Field(description="Sections to reference")


def fetch_and_cache(
    *,
    url: str,
    cache_file: str,
    timeout: float = 10.0,
):
    filename = Path(cache_file)
    if filename.exists():
        return filename.read_text()

    response = httpx.get(f"https://r.jina.ai/{url}", timeout=timeout)
    response.raise_for_status()

    contents = response.text

    Path(cache_file).write_text(contents)

    return contents


def load_data():
    trademark_policy = fetch_and_cache(
        url="https://www.djangoproject.com/trademarks/",
        cache_file="django-trademarks.md",
    )
    trademark_faqs = fetch_and_cache(
        url="https://www.djangoproject.com/trademarks/faq/",
        cache_file="django-trademarks-faq.md",
    )
    return {"trademark_policy": trademark_policy, "trademark_faqs": trademark_faqs}


def get_agent(*, output_type=Output):
    data = load_data()

    agent = Agent(
        model=OPENAI_MODEL_NAME,
        output_type=output_type,
        system_prompt=SYSTEM_PROMPT,
    )

    @agent.instructions
    def add_trademark_policy() -> str:
        return f"<trademark_policy>\n\n{data['trademark_policy']}\n\n</trademark_policy>"

    @agent.instructions
    def add_trademark_faqs() -> str:
        return f"<trademark_faqs>\n\n{data['trademark_faqs']}\n\n</trademark_faqs>"

    return agent


app = typer.Typer(help="Django Trademark Agent - Ask questions about DSF trademark policy")


@app.command()
def ask(question: str, model_name: str = OPENAI_MODEL_NAME):
    """Ask the trademark agent a question."""
    agent = get_agent()

    result = agent.run_sync(question)

    if result.output.approved:
        console.print(f"[yellow][bold]Approval status:[/bold][/yellow] [green]{result.output.approved}[/green]\n")
    else:
        console.print(f"[yellow][bold]Approval status:[/bold][/yellow] [red]{result.output.approved}[/red]\n")

    console.print(
        f"[green][bold]Answer:[/bold][/green] {result.output.answer}\n\n"
        f"[yellow][bold]Reasoning:[/bold][/yellow] {result.output.reasoning}\n"
    )

    if result.output.sections:
        console.print("[yellow][bold]Sections:[/bold][/yellow]")
        for section in result.output.sections:
            console.print(f"- {section}")


@app.command()
def web(
    host: str = "127.0.0.1",
    port: int = 8080,
):
    """Launch the trademark agent as a web chat interface."""
    agent = get_agent(output_type=None)
    web_app = agent.to_web()

    console.print(f"[bold green]Starting web interface at http://{host}:{port}[/bold green]")
    uvicorn.run(web_app, host=host, port=port)


@app.command()
def debug():
    """Print the compiled system prompt for debugging."""
    data = load_data()

    console.print("[bold cyan]===== SYSTEM PROMPT =====[/bold cyan]\n")
    console.print(SYSTEM_PROMPT)
    console.print("\n[bold cyan]===== INSTRUCTIONS =====[/bold cyan]\n")
    console.print(f"<trademark_policy>\n\n{data['trademark_policy']}\n\n</trademark_policy>")
    console.print(f"\n<trademark_faqs>\n\n{data['trademark_faqs']}\n\n</trademark_faqs>")
    console.print("\n[bold cyan]=========================[/bold cyan]")


if __name__ == "__main__":
    app()
