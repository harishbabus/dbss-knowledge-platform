# Attachment processing fixes

This revision addresses the four remaining failures from the 153-attachment integration run:

- Archive expanded-content guard increased from 50 MiB to 512 MiB. Extracted content is persisted through the chunked attachment-content repository, so a large archive no longer has to fit in one MongoDB document.
- Image extraction retries Pillow with truncated-image support and can fall back to SVG/XML content when an image extension does not match the actual payload.
- Attachment downloads create a fresh temporary `.part` file for every retry and retry local filesystem `OSError` failures.

The existing archive file-count safety limit remains in place.
