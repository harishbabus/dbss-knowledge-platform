from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from app.chunking.base_splitter import BaseSplitter
from app.chunking.character_splitter import CharacterSplitter
from app.models.knowledge_page import KnowledgePage


class HierarchicalSplitter(BaseSplitter):
    """
    Splits Confluence content using heading boundaries.

    Small sections remain as a single chunk.

    Sections larger than the configured chunk size are
    further divided using CharacterSplitter while
    preserving the section heading in every chunk.
    """

    def __init__(
        self,
        chunk_size: int = 1200,
        overlap: int = 200,
    ):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        if overlap < 0:
            raise ValueError("overlap cannot be negative")

        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.overlap = overlap

        self.character_splitter = CharacterSplitter(
            chunk_size=chunk_size,
            overlap=overlap,
        )

    @property
    def name(self) -> str:
        return "hierarchical"

    def split(
        self,
        page: KnowledgePage,
    ) -> list[str]:
        html = page.content.get(
            "raw_html",
            "",
        )

        if not html.strip():
            return []

        sections = self._extract_sections(html)

        chunks: list[str] = []

        for title, content in sections:
            section_chunks = self._split_section(
                title,
                content,
            )

            chunks.extend(section_chunks)

        return chunks

    def _split_section(
        self,
        title: str,
        content: str,
    ) -> list[str]:
        section_text = self._build_section_text(
            title,
            content,
        )

        if not section_text:
            return []

        #
        # Section fits into a single chunk.
        #
        if len(section_text) <= self.chunk_size:
            return [section_text]

        #
        # No heading.
        #
        if not title:
            return self.character_splitter.split(self._create_page(content))

        #
        # Reserve space for:
        #
        #     heading + newline
        #
        heading_length = len(title) + 1

        available_size = self.chunk_size - heading_length

        if available_size <= 0:
            raise ValueError("Heading is too large for configured chunk_size")

        #
        # Keep overlap within the available
        # content size.
        #
        content_overlap = min(
            self.overlap,
            available_size - 1,
        )

        splitter = CharacterSplitter(
            chunk_size=available_size,
            overlap=content_overlap,
        )

        #
        # IMPORTANT:
        #
        # Split only the content.
        # Do NOT pass the heading to CharacterSplitter.
        #
        content_chunks = splitter.split(self._create_page(content))

        #
        # Restore the heading on EVERY chunk.
        #
        return [f"{title}\n{chunk}" for chunk in content_chunks]

    @staticmethod
    def _extract_sections(
        html: str,
    ) -> list[tuple[str, str]]:
        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        sections: list[tuple[str, str]] = []

        current_title = ""
        current_content: list[str] = []

        def save_current_section() -> None:
            nonlocal current_title
            nonlocal current_content

            #
            # Preserve headings even when they have
            # no body content.
            #
            if current_title or current_content:
                sections.append(
                    (
                        current_title,
                        "\n".join(current_content).strip(),
                    )
                )

            current_title = ""
            current_content = []

        #
        # Walk the document in DOM order.
        #
        for element in soup.find_all(
            ["h1", "h2", "h3", "h4", "p", "li", "pre", "table"]
        ):
            if not isinstance(element, Tag):
                continue

            #
            # Skip elements that are nested inside another
            # element that will already be processed.
            #
            if element.find_parent(["p", "li", "pre", "table"]):
                continue

            #
            # Heading
            #
            if element.name in {
                "h1",
                "h2",
                "h3",
                "h4",
            }:
                save_current_section()

                current_title = element.get_text(
                    " ",
                    strip=True,
                )

                continue

            #
            # Content
            #
            text = element.get_text(
                " ",
                strip=True,
            )

            if text:
                current_content.append(text)

        #
        # Save final section.
        #
        save_current_section()

        return sections

    @staticmethod
    def _build_section_text(
        title: str,
        content: str,
    ) -> str:
        if title and content:
            return f"{title}\n{content}"

        return title or content

    @staticmethod
    def _create_page(
        text: str,
    ) -> KnowledgePage:
        return KnowledgePage.model_construct(
            id="hierarchical-split",
            content={
                "plain_text": text,
            },
        )
