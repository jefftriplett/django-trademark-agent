#!/usr/bin/env -S uv --quiet run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx2",
#     "environs",
#     "pydantic-ai-slim[openai,web]>=2,<3",
#     "rich",
#     "typer",
#     "uvicorn",
# ]
# ///

import time

import httpx2
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
OPENAI_MODEL_NAME: str = env.str("OPENAI_MODEL_NAME", default="openai:gpt-5.4-nano")

CACHE_MAX_AGE_HOURS: float = env.float("CACHE_MAX_AGE_HOURS", default=24.0)

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


def cache_is_fresh(filename: Path, max_age_hours: float) -> bool:
    """Return True if the cache file exists and is younger than max_age_hours."""
    if not filename.exists() or max_age_hours <= 0:
        return False

    return (time.time() - filename.stat().st_mtime) < (max_age_hours * 3600)


def fetch_and_cache(
    *,
    url: str,
    cache_file: str,
    timeout: float = 10.0,
    max_age_hours: float = CACHE_MAX_AGE_HOURS,
    refresh: bool = False,
):
    filename = Path(cache_file)
    if not refresh and cache_is_fresh(filename, max_age_hours):
        return filename.read_text()

    try:
        response = httpx2.get(f"https://r.jina.ai/{url}", timeout=timeout, follow_redirects=True)
        response.raise_for_status()
    except httpx2.HTTPError as exc:
        if filename.exists():
            console.print(f"[yellow]Could not refresh {filename}: {exc}. Using the cached copy.[/yellow]")
            return filename.read_text()
        raise

    contents = response.text

    filename.write_text(contents)

    return contents


def load_data(*, refresh: bool = False):
    trademark_policy = fetch_and_cache(
        url="https://www.djangoproject.com/trademarks/",
        cache_file="django-trademarks.md",
        refresh=refresh,
    )
    trademark_faqs = fetch_and_cache(
        url="https://www.djangoproject.com/trademarks/faq/",
        cache_file="django-trademarks-faq.md",
        refresh=refresh,
    )
    return {"trademark_policy": trademark_policy, "trademark_faqs": trademark_faqs}


def get_agent(*, output_type=Output, refresh: bool = False):
    data = load_data(refresh=refresh)

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


app = typer.Typer(
    help="Django Trademark Agent - Ask questions about DSF trademark policy",
    no_args_is_help=True,
)


@app.command()
def ask(
    question: str,
    model_name: str = OPENAI_MODEL_NAME,
    refresh: bool = typer.Option(False, help="Re-fetch the source documents, ignoring the cache."),
):
    """Ask the trademark agent a question."""
    agent = get_agent(refresh=refresh)

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
    refresh: bool = typer.Option(False, help="Re-fetch the source documents, ignoring the cache."),
):
    """Launch the trademark agent as a web chat interface."""
    # output_type=str keeps replies conversational. Pydantic AI v2 rejects None here —
    # it reads it as "no output types provided" and raises UserError.
    agent = get_agent(output_type=str, refresh=refresh)
    web_app = agent.to_web()

    console.print(f"[bold green]Starting web interface at http://{host}:{port}[/bold green]")
    uvicorn.run(web_app, host=host, port=port)


@app.command()
def debug(
    refresh: bool = typer.Option(False, help="Re-fetch the source documents, ignoring the cache."),
):
    """Print the compiled system prompt for debugging."""
    data = load_data(refresh=refresh)

    console.print("[bold cyan]===== SYSTEM PROMPT =====[/bold cyan]\n")
    console.print(SYSTEM_PROMPT)
    console.print("\n[bold cyan]===== INSTRUCTIONS =====[/bold cyan]\n")
    console.print(f"<trademark_policy>\n\n{data['trademark_policy']}\n\n</trademark_policy>")
    console.print(f"\n<trademark_faqs>\n\n{data['trademark_faqs']}\n\n</trademark_faqs>")
    console.print("\n[bold cyan]=========================[/bold cyan]")


if __name__ == "__main__":
    app()
