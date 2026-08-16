# DECISIONS.md

# DBSS Knowledge Platform — Architectural Decisions

## Decision 1 — MongoDB

Decision:
Use MongoDB as the preferred persistence layer.

Reason:
The platform stores structured page, attachment, extraction and future knowledge
objects and is already implemented around MongoDB.

Constraint:
Do not replace MongoDB with SQLite unless explicitly requested.

## Decision 2 — External attachment download directory

Decision:
Attachment downloads must remain outside the OneDrive-managed Downloads folder.

Reason:
The development workspace is inside OneDrive and the previous Downloads location
caused file handling/synchronization issues.

Configuration:
DBSS_ATTACHMENT_DOWNLOAD_DIR

Constraint:
Do not move downloads back to the old location.

## Decision 3 — Existing implementation is the baseline

Decision:
Treat the current repository as an existing system, not a greenfield project.

Constraint:
Inspect callers/tests before changing interfaces.

Avoid broad rewrites when a focused change is sufficient.

## Decision 4 — Attachment extraction should preserve provenance

Decision:
Extracted content must retain source information.

For archive members, preserve the internal filename.

Example:

FILE: config/application.properties
<content>

FILE: docs/API.pdf
<content>

Reason:
Downstream chunking/retrieval needs to know where content originated.

## Decision 5 — Archives need safety limits

Decision:
ZIP/RAR extraction must enforce resource limits.

Limits include:
- archive member count
- total expanded size
- individual member size

Reason:
Avoid uncontrolled archive expansion and resource exhaustion.

## Decision 6 — Do not arbitrarily truncate valid large archive text

Decision:
A valid textual archive member should not be silently truncated to a small fixed
output size merely to protect memory.

Resource safety should be enforced using archive/member limits and streaming or
bounded processing where appropriate.

## Decision 7 — Unknown/no-extension files

Decision:
Files without extensions should be considered extractable when content sniffing
shows that they are textual.

Reason:
Confluence repositories contain configuration/documentation files without normal
extensions.

## Decision 8 — Misleading file extensions

Decision:
Where practical, inspect content when a known extension appears inconsistent with
the payload.

Examples:
- JSON payload named .png
- SVG/XML payload named .png
- text/config payload with misleading extension

Do not blindly trust extensions.

## Decision 9 — Tests are the contract

Decision:
Existing tests should be treated as a behavioral contract.

Development order:
1. targeted tests
2. affected subsystem tests
3. broader suite
4. expensive real-crawler tests

## Decision 10 — Real-data validation before further redesign

Decision:
Before adding another major extraction feature or redesigning the attachment
pipeline, validate the extractor against the real downloaded Confluence corpus.

Reason:
Synthetic unit tests cannot expose all real-world file-format and payload problems.

## Decision 11 — Architecture is intentionally staged

Decision:
Stabilize ingestion and extraction before investing heavily in embeddings/vector
search/RAG.

Current order:

1. Confluence ingestion
2. Attachment ingestion
3. Attachment extraction
4. Real-data extraction validation
5. Content normalization
6. Chunking
7. Embeddings/vector store
8. Retrieval evaluation
9. RAG
10. Jira integration/correlation
11. AI documentation/assistant capabilities

## Decision 12 — ChatGPT and Codex roles

Decision:
Use ChatGPT primarily for:
- architecture
- product/AI design
- trade-offs
- project direction
- review

Use Codex primarily for:
- repository inspection
- implementation
- tests
- refactoring
- debugging
- Git changes

When a change has architectural implications, Codex should surface the decision
rather than silently changing the architecture.
