#!/usr/bin/env -S uv --quiet run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx2",
#     "environs",
#     "fastmcp",
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
PYDANTIC_AI_MODEL: str = env.str("PYDANTIC_AI_MODEL", default="openai:gpt-5.4-nano")

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
        model=PYDANTIC_AI_MODEL,
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
    model_name: str = PYDANTIC_AI_MODEL,
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


@app.command()
def mcp(
    refresh: bool = typer.Option(False, help="Re-fetch the source documents, ignoring the cache."),
    transport: str = typer.Option("stdio", help="MCP transport: stdio or http"),
    host: str = "127.0.0.1",
    port: int = 8000,
):
    """Serve this agent as an MCP server so other agents can ask it questions.

    Pydantic AI is an MCP client, not a server, so FastMCP handles the server side.
    """
    from fastmcp import FastMCP

    server = FastMCP("django-trademark-agent")
    cached = {}

    def build_agent():
        """Build on first use — loading the documents up front would stall the handshake."""
        if "agent" not in cached:
            cached["agent"] = get_agent(refresh=refresh)
        return cached["agent"]

    @server.tool
    async def trademark_question(question: str) -> Output:
        """Answer a question about Django's trademark policy."""
        result = await build_agent().run(question)
        return result.output

    # stdio transport speaks JSON-RPC on stdout — log to stderr so we don't corrupt it.
    Console(stderr=True).print(f"[bold green]Serving MCP over {transport}[/bold green]")

    if transport == "http":
        server.run(transport="http", host=host, port=port)
    else:
        server.run()


# Maps a pydantic-ai model prefix to the env var holding that provider's key, so
# doctor notices when the model points at a provider you have no credentials for.
DOCTOR_PROVIDER_KEYS: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "cohere": "CO_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "google": "GEMINI_API_KEY",
    "google-gla": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "openai": "OPENAI_API_KEY",
}

DOCTOR_OPTIONAL_ENV: list[str] = []


def doctor_mask(value: str) -> str:
    """Show enough of a secret to recognize it, never enough to use it."""
    if len(value) <= 8:
        return "set"
    return f"{value[:4]}...{value[-4:]}"


def run_doctor(probe: bool = True) -> bool:
    """Report config/credential/connectivity status. Returns False on any failure."""
    results: list[tuple[str, str, str]] = []

    results.append(("pass", "Model", PYDANTIC_AI_MODEL))

    provider = PYDANTIC_AI_MODEL.split(":", 1)[0] if ":" in PYDANTIC_AI_MODEL else ""
    expected_key = DOCTOR_PROVIDER_KEYS.get(provider)
    if expected_key is None:
        results.append(
            ("warn", "Provider", f"unrecognized provider {provider!r}; cannot check its key")
        )
    elif value := env.str(expected_key, default=""):
        results.append(("pass", expected_key, doctor_mask(value)))
    else:
        results.append(("fail", expected_key, f"not set -- add {expected_key} to .env"))

    for name in DOCTOR_OPTIONAL_ENV:
        if value := env.str(name, default=""):
            results.append(("pass", name, doctor_mask(value)))
        else:
            results.append(("warn", name, "not set (optional; some features disabled)"))

    if probe:
        try:
            Agent(model=PYDANTIC_AI_MODEL).run_sync("Reply with: ok")
            results.append(("pass", "Live probe", "backend reachable and responding"))
        except Exception as exc:
            results.append(("fail", "Live probe", f"{type(exc).__name__}: {exc}"))
    else:
        results.append(("warn", "Live probe", "skipped (--no-probe)"))

    console.print("\n[bold]Doctor[/bold]\n")
    styles = {"pass": "green", "warn": "yellow", "fail": "red"}
    for status, label, detail in results:
        console.print(
            f"[{styles[status]}]{status.upper():<4}[/{styles[status]}] {label:<18} {detail}"
        )

    failed = sum(1 for status, _, _ in results if status == "fail")
    warned = sum(1 for status, _, _ in results if status == "warn")
    if failed:
        console.print(f"\n[red]{failed} failed[/red], {warned} warning(s)\n")
        return False
    console.print(f"\n[green]All checks passed[/green] ({warned} warning(s))\n")
    return True


@app.command()
def doctor(probe: bool = True):
    """Check configuration and credentials, then probe the LLM backend."""
    if not run_doctor(probe=probe):
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
