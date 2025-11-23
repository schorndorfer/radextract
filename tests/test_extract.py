"""Tests for the extract module."""

from radextract.extract import extract_entities


def test_extract_entities_returns_correct_structure():
    """Test that extract_entities returns the expected data structure."""
    text = "The patient has a fracture."
    result = extract_entities(text)

    assert isinstance(result, dict)
    assert "text" in result
    assert "entities" in result
    assert isinstance(result["entities"], list)


def test_extract_entities_preserves_original_text():
    """Test that the original text is preserved in the output."""
    text = "The patient has a fracture in the left femur."
    result = extract_entities(text)

    assert result["text"] == text


def test_extract_entities_empty_text():
    """Test extraction with empty text."""
    result = extract_entities("")

    assert result["text"] == ""
    assert result["entities"] == []


def test_extract_entities_tuple_format():
    """Test that entities are tuples with correct format when present."""
    text = "Sample text"
    result = extract_entities(text)

    # Verify entities is a list
    assert isinstance(result["entities"], list)

    # If there are entities, each should be a tuple of (start, end, entity_text, label)
    for entity in result["entities"]:
        assert isinstance(entity, tuple)
        assert len(entity) == 4
        start, end, entity_text, label = entity
        assert isinstance(start, int)
        assert isinstance(end, int)
        assert isinstance(entity_text, str)
        assert isinstance(label, str)
        assert start >= 0
        assert end >= start
