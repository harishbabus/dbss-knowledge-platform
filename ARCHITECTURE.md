# ARCHITECTURE.md

# DBSS Knowledge Platform Architecture

## 1. Purpose

The platform is intended to create a searchable, AI-ready representation of
DBSS/DCLM product knowledge.

The initial knowledge source is Confluence because it already contains substantial
product documentation such as:
- API specifications
- configuration information
- troubleshooting guides
- product documentation
- attachments and supporting files

Jira will later provide requirements and engineering context.

## 2. Current ingestion architecture

### Confluence pages

Confluence
  |
  v
Confluence client
  |
  v
Crawler / inventory
  |
  v
Page processing
  |
  v
MongoDB

Delta synchronization is part of the current system.

### Confluence attachments

Confluence attachment metadata
  |
  v
Attachment downloader
  |
  v
External download directory
  |
  v
AttachmentContentExtractor
  |
  v
ExtractedContent
  |
  v
Attachment content persistence

The external download directory is intentional because the project is developed
in a OneDrive-managed Windows workspace.

## 3. Content extraction architecture

AttachmentContentExtractor selects an extractor based on:
1. filename/path extension
2. special filename patterns
3. content sniffing where appropriate

Current content categories include:

Text:
- TXT
- CSV
- XML
- HTML
- LDIF
- configuration-like/no-extension files

Structured:
- JSON
- XLSX

Documents:
- PDF
- DOCX
- PPTX

Archives:
- ZIP
- RAR

Images:
- PNG
- JPG/JPEG
- GIF
- BMP
- TIF/TIFF

Images use OCR where applicable.

Mislabeled payloads are handled using content sniffing/fallbacks where possible.

## 4. Archive architecture

Archives are not treated as one opaque binary.

The extractor:
- checks archive member count
- checks expanded size
- checks member size
- reads members
- identifies useful textual content
- preserves internal filenames

Conceptually:

ZIP/RAR
  |
  +--> config/application.properties
  |
  +--> docs/API.pdf
  |
  +--> config/database.xml
  |
  +--> README.txt
  |
  v
searchable extracted representation

Internal filenames are important metadata because they help downstream retrieval
explain where a piece of content originated.

## 5. Persistence

MongoDB is the preferred document persistence layer.

Existing repositories and models should be inspected before changing schemas.

Do not replace MongoDB with SQLite unless explicitly requested.

## 6. Future knowledge pipeline

The expected future pipeline is:

Extracted content
  |
  v
Normalization
  |
  v
Chunking
  |
  v
Metadata enrichment
  |
  v
Embedding generation
  |
  v
Vector database
  |
  v
Hybrid / semantic retrieval
  |
  v
RAG context construction
  |
  v
LLM
  |
  +--> Q&A
  +--> API documentation
  +--> configuration documentation
  +--> troubleshooting documentation
  +--> product knowledge assistant

## 7. Future Jira integration

Jira is expected to become another knowledge source:

Jira
  |
  +--> Epics
  +--> Stories
  +--> Requirements
  +--> Bugs/defects
  +--> Acceptance criteria
  |
  v
normalized knowledge
  |
  v
link/correlate with Confluence knowledge

The exact Jira architecture has not yet been finalized.

## 8. Metadata principles

Every extracted piece of knowledge should preserve enough provenance for future
retrieval and citation.

Useful metadata includes:
- source system
- page ID
- page title
- attachment ID
- attachment filename
- original path
- content type
- extraction status
- extraction metadata
- archive member filename where applicable
- parent page information

Do not discard provenance merely to simplify chunking.

## 9. Design principles

Prefer:
- deterministic ingestion
- idempotent/delta-aware processing
- explicit statuses
- graceful failure
- strong provenance
- testability
- bounded resource use
- modular extractors
- backward compatibility

Avoid:
- large rewrites without need
- hidden fallback behavior
- silent data loss
- uncontrolled archive expansion
- hard-coded local paths
- secrets in source control
