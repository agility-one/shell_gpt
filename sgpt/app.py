"""
shell-gpt: An interface to OpenAI's ChatGPT (GPT-3.5) API

This module provides a simple interface for OpenAI's ChatGPT API using Typer
as the command line interface. It supports different modes of output including
shell commands and code, and allows users to specify the desired OpenAI model
and length and other options of the output. Additionally, it supports executing
shell commands directly from the interface.

API Key is stored locally for easy use in future runs.
"""
# To allow users to use arrow keys in the REPL.
import readline  # noqa: F401
import sys

import typer

# Click is part of typer.
from click import BadArgumentUsage, MissingParameter

from sgpt import ChatHandler, DefaultHandler, OpenAIClient, ReplHandler, cfg
from sgpt.utils import ModelOptions, get_edited_prompt, run_command


def main(
    prompt: str = typer.Argument(
        None,
        show_default=False,
        help="The prompt to generate completions for.",
    ),
    model: ModelOptions = typer.Option(
        ModelOptions(cfg.get("DEFAULT_MODEL")).value,
        help="OpenAI GPT model to use.",
    ),
    temperature: float = typer.Option(
        0.1,
        min=0.0,
        max=1.0,
        help="Randomness of generated output.",
    ),
    top_probability: float = typer.Option(
        1.0,
        min=0.1,
        max=1.0,
        help="Limits highest probable tokens (words).",
    ),
    shell: bool = typer.Option(
        False,
        "--shell",
        "-s",
        help="Generate and execute shell commands.",
        rich_help_panel="Assistance Options",
    ),
    code: bool = typer.Option(
        False,
        help="Generate only code.",
        rich_help_panel="Assistance Options",
    ),
    editor: bool = typer.Option(
        False,
        help="Open $EDITOR to provide a prompt.",
    ),
    cache: bool = typer.Option(
        True,
        help="Cache completion results.",
    ),
    chat: str = typer.Option(
        None,
        help="Follow conversation with id, " 'use "temp" for quick session.',
        rich_help_panel="Chat Options",
    ),
    repl: str = typer.Option(
        None,
        help="Start a REPL (Read–eval–print loop) session.",
        rich_help_panel="Chat Options",
    ),
    show_chat: str = typer.Option(
        None,
        help="Show all messages from provided chat id.",
        callback=ChatHandler.show_messages_callback,
        rich_help_panel="Chat Options",
    ),
    list_chat: bool = typer.Option(
        False,
        help="List all existing chat ids.",
        callback=ChatHandler.list_ids,
        rich_help_panel="Chat Options",
    ),
) -> None:
    stdin_passed = not sys.stdin.isatty()

    if stdin_passed and not repl:
        prompt = sys.stdin.read() + (prompt or "")

    if not prompt and not editor and not repl:
        raise MissingParameter(param_hint="PROMPT", param_type="string")

    if shell and code:
        raise BadArgumentUsage("--shell and --code options cannot be used together.")

    if chat and repl:
        raise BadArgumentUsage("--chat and --repl options cannot be used together.")

    if editor and stdin_passed:
        raise BadArgumentUsage("--editor option cannot be used with stdin input.")

    if editor:
        prompt = get_edited_prompt()

    api_host = cfg.get("OPENAI_API_HOST")
    api_key = cfg.get("OPENAI_API_KEY")
    client = OpenAIClient(api_host, api_key)

    if repl:
        # Will be in infinite loop here until user exits with Ctrl+C.
        ReplHandler(client, repl, shell, code).handle(
            prompt,
            model=model.value,
            temperature=temperature,
            top_probability=top_probability,
            chat_id=repl,
            caching=cache,
        )

    if chat:
        full_completion = ChatHandler(client, chat, shell, code).handle(
            prompt,
            model=model.value,
            temperature=temperature,
            top_probability=top_probability,
            chat_id=chat,
            caching=cache,
        )
    else:
        full_completion = DefaultHandler(client, shell, code).handle(
            prompt,
            model=model.value,
            temperature=temperature,
            top_probability=top_probability,
            caching=cache,
        )

    if shell and not stdin_passed and typer.confirm("Execute shell command?"):
        run_command(full_completion)


def entry_point() -> None:
    # Python package entry point defined in setup.py
    typer.run(main)


if __name__ == "__main__":
    entry_point()
