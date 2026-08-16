# AGENTS.md

## Project

DBSS Knowledge Platform

This is an existing Python project for building an AI-ready knowledge platform for
DBSS/DCLM product documentation. The primary source currently being ingested is
Confluence. Jira integration is planned.

## Current engineering objective

Build a robust ingestion and knowledge pipeline:

Confluence
  -> page crawling / delta synchronization
  -> attachment downloading
  -> attachment content extraction
  -> content persistence
  -> chunking
  -> embeddings / vector store
  -> retrieval / RAG
  -> LLM-powered Q&A and documentation generation

Future sources/capabilities include Jira requirements, epics, stories and defects.

## How to work

1. Inspect the existing implementation before changing it.
2. Understand callers, models, repositories and tests before changing public interfaces.
3. Prefer small, focused, testable changes.
4. Preserve existing working behavior unless the task explicitly requires a change.
5. Do not redesign architecture merely for style.
6. Do not silently remove functionality.
7. When a change affects an interface, inspect all callers and tests.
8. Run targeted tests first.
9. Avoid expensive real-crawler tests during normal development iterations.
10. Run the full suite only after targeted tests are passing.
11. Report exactly what changed and which tests were run.

## Environment

- Python project.
- Development is currently on Windows.
- The project uses a local .venv.
- MongoDB is the preferred persistence layer.
- Do not replace MongoDB with SQLite unless explicitly requested.
- Do not expose or commit credentials or secrets.
- Keep .env local and protected by .gitignore.

## Attachment downloads

Attachment downloads were deliberately moved outside the OneDrive-managed Downloads
folder because of OneDrive-related file handling issues.

Do not move them back to the old downloads location.

The downloader supports a configurable external download directory using:
DBSS_ATTACHMENT_DOWNLOAD_DIR

Inspect the current implementation and .env.example before changing this behavior.

## Attachment extraction

The attachment extractor must be robust against real Confluence data.

Supported/currently handled categories include:
- TXT
- CSV
- JSON
- XML
- HTML
- LDIF
- XLSX
- PDF
- DOCX
- PPTX
- ZIP
- RAR
- common image formats
- unknown/no-extension text files
- content sniffing for misleading extensions
- OCR for images

Archive extraction must:
- enforce safety limits
- preserve internal member filenames
- avoid uncontrolled expansion
- extract useful text from supported members
- continue safely when an individual member is binary/unsupported

Do not reintroduce arbitrary low output limits that cause valid large textual
archive members to be truncated unless explicitly required.

## Testing

Use the existing tests as the contract.

Preferred sequence:
1. targeted test
2. affected subsystem tests
3. broader suite
4. expensive real crawler tests only when explicitly appropriate

The real crawler tests can be slow because they may contact/process large Confluence
datasets. Do not run them automatically after every small change.

## Current coding principle

For ingestion and extraction, favor:
- deterministic behavior
- explicit error/status reporting
- useful metadata
- backward compatibility
- graceful handling of malformed or unexpected attachments
- security/resource limits for archives
- observability through existing logging

## Secrets

Never print, commit, or copy:
- Confluence passwords
- API tokens
- MongoDB credentials
- OpenAI/Gemini keys
- Telegram bot tokens
- other secrets

## Before a substantial change

Read:
- PROJECT_STATUS.md
- ARCHITECTURE.md
- DECISIONS.md

Then inspect the relevant implementation and tests.

Do not modify files merely to "clean up" unless the cleanup is directly relevant
to the current task.
