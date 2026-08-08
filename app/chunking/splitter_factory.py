from app.chunking.base_splitter import BaseSplitter
from app.chunking.character_splitter import CharacterSplitter
from app.chunking.heading_splitter import HeadingSplitter
from app.chunking.hierarchical_splitter import (
    HierarchicalSplitter,
)


class SplitterFactory:
    """
    Creates chunking strategies by name.
    """

    _splitters: dict[str, type[BaseSplitter]] = {
        "character": CharacterSplitter,
        "heading": HeadingSplitter,
        "hierarchical": HierarchicalSplitter,
    }

    @classmethod
    def create(
        cls,
        splitter_name: str,
    ) -> BaseSplitter:
        splitter_class = cls._splitters.get(splitter_name)

        if splitter_class is None:
            supported = ", ".join(sorted(cls._splitters))

            raise ValueError(
                f"Unknown splitter '{splitter_name}'. Supported splitters: {supported}"
            )

        return splitter_class()
