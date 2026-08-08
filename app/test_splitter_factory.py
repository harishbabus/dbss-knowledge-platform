from app.chunking.character_splitter import CharacterSplitter
from app.chunking.heading_splitter import HeadingSplitter
from app.chunking.splitter_factory import SplitterFactory


def test_create_character_splitter():
    splitter = SplitterFactory.create("character")

    assert isinstance(
        splitter,
        CharacterSplitter,
    )


def test_create_heading_splitter():
    splitter = SplitterFactory.create("heading")

    assert isinstance(
        splitter,
        HeadingSplitter,
    )


def test_unknown_splitter():
    try:
        SplitterFactory.create("unknown")
    except ValueError as exc:
        assert "Unknown splitter" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown splitter")
