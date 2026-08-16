# PROJECT_STATUS.md

## DBSS Knowledge Platform — Current Handoff

Date: 2026-08-16

## 1. Project purpose

The DBSS Knowledge Platform is being built as an AI-ready knowledge platform for
DBSS/DCLM product knowledge.

The long-term objective is to combine existing product documentation with Jira
requirements and engineering/product context so that AI can support:

- product knowledge search
- API documentation
- configuration documentation
- troubleshooting documentation
- documentation generation
- knowledge Q&A
- future AI engineering/product workflows

## 2. Current high-level flow

Current source:

Confluence
  -> page crawler
  -> page processing
  -> MongoDB

Attachments:

Confluence attachment metadata
  -> attachment downloader
  -> attachment content extractor
  -> attachment content persistence

Knowledge pipeline:

extracted content
  -> chunking
  -> embeddings/vector store
  -> retrieval
  -> RAG / LLM

Jira integration is planned but is not the current task.

## 3. Existing project areas

The repository contains components for:
- Confluence connectivity/crawling
- inventory and delta synchronization
- page processing
- attachment downloading
- attachment processing
- attachment repositories
- attachment content extraction
- content/chunk pipelines
- MongoDB persistence
- tests for the above

Do not assume a component should be replaced simply because a different design is
possible. Inspect the current implementation first.

## 4. Current attachment state

Attachment downloading is implemented.

The download directory was externalized because the project is being developed
inside a OneDrive-managed Windows workspace and the previous Downloads location
caused problems.

The current downloader supports:
DBSS_ATTACHMENT_DOWNLOAD_DIR

Attachment content extraction has recently been stabilized.

Current extractor capabilities include:
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
- PNG/JPG/JPEG/GIF/BMP/TIF/TIFF
- unknown/no-extension text
- content sniffing for mislabeled payloads
- image OCR
- archive member extraction

The extractor also records useful extraction metadata and statuses.

## 5. Latest test status

Attachment extractor tests:
8 passed.

Command:

python -m pytest app/test_attachment_content.py app/test_attachment_content_extractor_extended.py -v

Latest result:
8 passed in 6.87 seconds.

Broader attachment-layer tests:
43 passed.

These covered:
- attachment content
- extended extractor behavior
- attachment content repository
- downloader
- attachment processor
- attachment repository

Latest result:
43 passed in 9.32 seconds.

The full test suite previously collected 107 tests. During one full run,
89 tests had passed before the run reached the long-running real crawler area and
was interrupted after more than 21 minutes. Therefore do not treat that interrupted
run as a complete-suite failure; it simply was not allowed to finish.

## 6. Recent extractor fixes

Recent work fixed/implemented:

1. ZIP/RAR expanded-size safety checks.
2. Archive file-count limits.
3. Large valid textual archive members are allowed without an arbitrary 5 MB
   output truncation.
4. ZIP/RAR internal member names are preserved in extracted text.
5. Unknown/no-extension text detection.
6. Mislabeled image/content sniffing.
7. SVG/XML payload fallback.
8. JSON payload with misleading image extension.
9. DOCX paragraph and table extraction.
10. Attachment extraction status/error handling.
11. Archive member decoding for useful textual content.

## 7. Current immediate task

The next task is NOT to redesign the extractor.

The next task is:

### Validate the extractor against the real downloaded Confluence attachment corpus.

Goal:
Find real-world extraction failures that synthetic unit tests cannot reveal.

The validation should produce a useful report containing at least:

- filename
- full/local path where appropriate
- extension
- file size
- detected/selected content type
- extraction status
- extraction error
- extracted character count
- metadata
- archive member count where applicable

Categorize results into:
- SUCCESS
- UNSUPPORTED
- EXTRACTION_FAILED
- EMPTY_CONTENT (if useful)

Also identify the attachment types with the highest failure rates.

## 8. Important constraint for the next task

Do not modify production extraction code before first understanding the real corpus
and the observed failures.

If a failure is found:
1. reproduce it with the smallest representative file possible
2. inspect the existing extractor logic
3. add a focused regression test
4. make the smallest appropriate production change
5. rerun targeted tests
6. rerun the broader attachment tests

## 9. Real-data validation

Use the configured external attachment download directory.

Do not scan or recreate the old OneDrive Downloads location.

Before running a potentially expensive corpus-wide validation:
- inspect the downloader/configuration to determine the actual directory
- estimate number and total size of files
- avoid loading the entire corpus into memory
- process one attachment at a time
- write a report incrementally if needed

## 10. After real attachment validation

Once extraction quality is understood and stable, the next architectural work is
expected to focus on:

1. extracted-content quality/normalization
2. chunking strategy
3. metadata preservation
4. embedding strategy
5. vector database integration
6. retrieval evaluation
7. RAG
8. Jira ingestion/correlation
9. AI-generated documentation

Do not jump to these stages while attachment extraction still has unexplained
real-data failures.

## 11. Working relationship with ChatGPT

ChatGPT is being used for architecture/product-level direction and review.

Codex is being used for repository-level implementation, testing, refactoring and
debugging.

When a design choice is ambiguous or could materially affect architecture, stop
and explain the options rather than making a broad architectural change silently.
