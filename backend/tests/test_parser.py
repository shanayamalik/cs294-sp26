from app.models import infer_section_type


def test_infer_section_type_supports_granular_specification_sections() -> None:
    assert infer_section_type("BACKGROUND OF THE INVENTION") == "BACKGROUND"
    assert infer_section_type("SUMMARY OF THE INVENTION") == "SUMMARY"
    assert infer_section_type("DETAILED DESCRIPTION") == "DESCRIPTION"