# LLM Resume File Assistant

A small Python project demonstrating LLM tool/function calling for local resume file operations. It supports PDF, TXT, and DOCX text extraction and includes dummy resumes.

## Features

- `read_file(filepath)`: extract content and metadata from PDF, TXT, and DOCX.
- `list_files(directory, extension=None)`: list files with name, size, extension, and modification timestamp.
- `write_file(filepath, content)`: create parent directories and write UTF-8 text.
- `search_in_file(filepath, keyword)`: case-insensitive keyword search with surrounding context.
- `llm_file_assistant.py`: uses the OpenAI Responses API and function tools to choose and call the file tools based on natural-language requests.
- 6 fictional sample resumes across PDF, TXT, and DOCX formats.

## Requirements

- Python 3.10+
- An OpenAI API key for LLM tool-calling mode. The file tools and tests work without an API key.

## Setup

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
```

Add your key to `.env`. The application loads `.env` automatically if `python-dotenv` is installed? To keep the setup minimal, export the variable in your shell or add `from dotenv import load_dotenv; load_dotenv()` near the imports in `llm_file_assistant.py`.

macOS/Linux:
```bash
export OPENAI_API_KEY="your-key"
python llm_file_assistant.py
```

Windows PowerShell:
```powershell
$env:OPENAI_API_KEY="your-key"
python llm_file_assistant.py
```

## Usage

Run interactively:

```bash
python llm_file_assistant.py
```

Or provide a single query:

```bash
python llm_file_assistant.py --query "Read all resumes in sample_resumes"
python llm_file_assistant.py --query "Find resumes mentioning Python experience"
python llm_file_assistant.py --query "Create a summary file for resume_john_doe.pdf"
```

Generated summary files should be written under `output/`.

## Use file tools without an LLM

```python
from fs_tools import read_file, list_files, search_in_file, write_file

print(list_files("sample_resumes", ".pdf"))
print(read_file("sample_resumes/resume_john_doe.pdf"))
print(search_in_file("sample_resumes/resume_john_doe.pdf", "Python"))
print(write_file("output/example.txt", "Example output"))
```

Relative paths passed to the LLM dispatcher resolve against the project directory. The `write_file` tool exposed to the LLM is restricted to the project directory. The lower-level `fs_tools.write_file` is a general filesystem utility and should only be used with trusted paths.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Demo video (2–3 minutes)

A `demo_script.md` is included with a timed walkthrough and sample commands. Record your screen while running the app with an API key. The LLM response depends on the model and API account, so the project does not ship a fabricated recording or pretend a live API call has been made.

## Design notes and limitations

- PDF extraction reads the text layer; scanned/image-only PDFs require OCR and are not handled here.
- Tool responses are JSON-serializable.
- File listing is non-recursive and only lists files directly in the requested directory.
- The assistant uses the OpenAI Responses API function-tool format.
- Treat resumes as sensitive personal data. The included resumes are fictional; do not upload real resumes to an LLM unless you have authorization and appropriate privacy controls.
