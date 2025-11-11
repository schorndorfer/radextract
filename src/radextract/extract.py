"""Entity extraction module for radiology reports."""


def extract_entities(text: str) -> dict:
    """Extract clinical entities from radiology report text.

    Args:
        text: The input text to extract entities from

    Returns:
        A dictionary with the following structure:
        {
            "text": str,  # The original input text
            "entities": list[tuple]  # List of (start, end, entity_text, label) tuples
        }

    Example:
        >>> result = extract_entities("The patient has a fracture in the left femur.")
        >>> result["text"]
        'The patient has a fracture in the left femur.'
        >>> result["entities"]
        [(20, 28, 'fracture', 'Observation::definitely present'),
         (37, 47, 'left femur', 'Anatomy::definitely present')]
    """
    # TODO: Implement actual entity extraction using a trained model
    # For now, return the structure with empty entities
    return {
        "text": text,
        "entities": []
    }
