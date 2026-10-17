"""LLM-powered resume file assistant using OpenAI function/tool calling.

Usage:
    python llm_file_assistant.py
    python llm_file_assistant.py --query "Read all resumes in sample_resumes"
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from fs_tools import read_file, list_files, write_file, search_in_file

ROOT = Path(__file__).resolve().parent
DEFAULT_RESUME_DIR = ROOT / "sample_resumes"
OUTPUT_DIR = ROOT / "output"

TOOL_SCHEMAS = [
    {"type": "function", "name": "read_file", "description": "Extract text and metadata from one PDF, TXT, or DOCX file.",
     "parameters": {"type": "object", "properties": {"filepath": {"type": "string"}},
                    "required": ["filepath"], "additionalProperties": False,}},
    {"type": "function", "name": "list_files", "description": "List files in a directory, optionally filtered by extension such as .pdf.",
     "parameters": {"type": "object", "properties": {"directory": {"type": "string"},
                    "extension": {"type": ["string", "null"]}},
                    "required": ["directory", "extension"], "additionalProperties": False,}},
    {"type": "function", "name": "write_file", "description": "Write text content to a file, creating parent directories if needed.",
     "parameters": {"type": "object", "properties": {"filepath": {"type": "string"}, "content": {"type": "string"}},
                    "required": ["filepath", "content"], "additionalProperties": False,}},
    {"type": "function", "name": "search_in_file", "description": "Search a resume for a keyword, case-insensitively, with surrounding context.",
     "parameters": {"type": "object", "properties": {"filepath": {"type": "string"}, "keyword": {"type": "string"}},
                    "required": ["filepath", "keyword"], "additionalProperties": False,}},
]

TOOL_FUNCTIONS = {
    "read_file": read_file,
    "list_files": list_files,
    "write_file": write_file,
    "search_in_file": search_in_file,
}


def _resolve_path(value: str) -> str:
    """Resolve relative paths against project root; absolute paths are preserved."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return str(path.resolve())


def dispatch_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Validate and execute an allowed tool call; paths are resolved locally."""
    if name not in TOOL_FUNCTIONS:
        return {"success": False, "error": "unknown_tool", "message": f"Tool not allowed: {name}"}
    args = dict(arguments)
    if name in {"read_file", "search_in_file"}:
        args["filepath"] = _resolve_path(args["filepath"])
    elif name == "list_files":
        args["directory"] = _resolve_path(args["directory"])
    elif name == "write_file":
        args["filepath"] = _resolve_path(args["filepath"])
        # Keep generated files inside the project directory.
        target = Path(args["filepath"])
        if ROOT not in target.parents and target != ROOT:
            return {"success": False, "error": "path_not_allowed",
                    "message": "For safety, write_file can only write inside the project directory."}
    return TOOL_FUNCTIONS[name](**args)


def run_assistant(query: str, model: str = "gpt-4.1-mini", max_tool_rounds: int = 8) -> str:
    """Run a tool-calling conversation using the OpenAI Responses API."""
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from exc
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your environment or .env file.")
    client = OpenAI()
    instructions = (
        "You are a careful resume file assistant. Use the provided tools for file operations; "
        f"the default resume directory is {DEFAULT_RESUME_DIR}. Resolve relative resume paths against "
        "the project root. When asked to read all resumes, list supported files and read them. "
        "When asked to find a skill, search relevant files. Never claim a tool succeeded unless its "
        "result says success. Summarize findings clearly and do not invent resume details. "
        "For summary-file requests, write a concise factual summary to the output/ directory."
    )
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=query,
        tools=TOOL_SCHEMAS,
    )
    for _ in range(max_tool_rounds):
        calls = [item for item in response.output if getattr(item, "type", None) == "function_call"]
        if not calls:
            return response.output_text or "(The model returned no text.)"
        outputs = []
        for call in calls:
            try:
                arguments = json.loads(call.arguments)
                result = dispatch_tool(call.name, arguments)
            except Exception as exc:
                result = {"success": False, "error": "tool_execution_error", "message": str(exc)}
            outputs.append({"type": "function_call_output", "call_id": call.call_id,
                            "output": json.dumps(result, ensure_ascii=False)})
        response = client.responses.create(
            model=model,
            instructions=instructions,
            previous_response_id=response.id,
            input=outputs,
            tools=TOOL_SCHEMAS,
        )
    return "Stopped after reaching the maximum number of tool-call rounds. Please narrow the request."


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM assistant for local resume files")
    parser.add_argument("--query", help="Ask a question; omit to start interactive mode")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
    args = parser.parse_args()
    if args.query:
        print(run_assistant(args.query, args.model))
        return
    print("Resume File Assistant (type 'exit' to quit)")
    while True:
        try:
            query = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if query.lower() in {"exit", "quit"}:
            break
        if query:
            try:
                print("\nAssistant> " + run_assistant(query, args.model))
            except Exception as exc:
                print(f"\nError: {exc}")


if __name__ == "__main__":
    main()
