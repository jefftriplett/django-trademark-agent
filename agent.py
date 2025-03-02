#!/usr/bin/env -S uv --quiet run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx",
#     "environs",
#     "pydantic-ai-slim[openai]",
#     "rich",
#     "typer",
# ]
# ///

import httpx
import typer

from environs import env
from pathlib import Path
from pydantic import BaseModel
from pydantic import Field
from pydantic_ai import Agent
from rich import print


OPENAI_API_KEY: str = env.str("OPENAI_API_KEY")
OPENAI_MODEL_NAME: str = env.str("OPENAI_MODEL_NAME", default="o3-mini")

SYSTEM_PROMPT = """
<system_context>

You are a Trademark policy assistant for the Django Software Foundation.

</system_context>

<behavior_guidelines>

- Please answer all questions using Django's trademark policy and frequently asked questions.

- Please warn the user that this not official or legal advice.

</behavior_guidelines>

<trademark_policy>

{trademark_policy}

</trademark_policy>

<trademark_faqs>

{trademark_faqs}

</trademark_faqs>
"""


class Result(BaseModel):
    approved: bool
    answer: str = Field(description="The answer to our question")
    reasoning: str = Field(description="The reasoning and support for our answer based on our source material")
    sections: list[str] = Field(description="Sections to reference if there is a violation")


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


def get_django_trademark_agent():
    trademark_policy = fetch_and_cache(
        url="https://www.djangoproject.com/trademarks/",
        cache_file="django-trademarks.md",
    )

    trademark_faqs = fetch_and_cache(
        url="https://www.djangoproject.com/trademarks/faq/",
        cache_file="django-trademarks-faq.md",
    )

    system_prompt = SYSTEM_PROMPT.format(
        trademark_policy=trademark_policy,
        trademark_faqs=trademark_faqs,
    )

    agent = Agent(
        model=OPENAI_MODEL_NAME,
        result_type=Result,
        system_prompt=system_prompt,
    )

    return agent


def main(question: str, model_name: str = OPENAI_MODEL_NAME):
    agent = get_django_trademark_agent()

    result = agent.run_sync(question)

    if result.data.approved:
        print(f"[yellow][bold]Approval status:[/bold][/yellow] [green]{result.data.approved}[/green]\n")
    else:
        print(f"[yellow][bold]Approval status:[/bold][/yellow] [red]{result.data.approved}[/red]\n")

    print(
        f"[green][bold]Answer:[/bold][/green] {result.data.answer}\n\n"
        f"[yellow][bold]Reasoning:[/bold][/yellow] {result.data.reasoning}\n"
    )

    if result.data.sections:
        print("[yellow][bold]Sections:[/bold][/yellow]")
        for section in result.data.sections:
            print(f"- {section}")


if __name__ == "__main__":
    typer.run(main)
