from bs4 import BeautifulSoup, Tag

from app.chunking.base_splitter import BaseSplitter
from app.models.knowledge_page import KnowledgePage


class HeadingSplitter(BaseSplitter):
    """
    Splits a KnowledgePage into chunks using HTML heading boundaries.

    Headings h1 through h4 start new sections.
    """

    @property
    def name(self) -> str:
        return "heading"

    def split(
        self,
        page: KnowledgePage,
    ) -> list[str]:
        html = page.content.get("raw_html", "")

        if not html.strip():
            return []

        soup = BeautifulSoup(html, "html.parser")

        chunks: list[str] = []
        current_lines: list[str] = []

        for element in (
            soup.body.find_all(recursive=False)
            if soup.body
            else soup.find_all(recursive=False)
        ):
            if not isinstance(element, Tag):
                continue

            if element.name in {
                "h1",
                "h2",
                "h3",
                "h4",
            }:
                self._append_chunk(
                    chunks,
                    current_lines,
                )

                current_lines = []

                heading = element.get_text(
                    " ",
                    strip=True,
                )

                if heading:
                    current_lines.append(heading)

                continue

            text = element.get_text(
                " ",
                strip=True,
            )

            if text:
                current_lines.append(text)

        self._append_chunk(
            chunks,
            current_lines,
        )

        return chunks

    @staticmethod
    def _append_chunk(
        chunks: list[str],
        lines: list[str],
    ) -> None:
        text = "\n".join(line for line in lines if line.strip()).strip()

        if text:
            chunks.append(text)
