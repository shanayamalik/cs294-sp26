from pathlib import Path

import pytest

from app.source_loader import load_source_text


def test_load_source_text_txt(tmp_path: Path) -> None:
    source = tmp_path / "sample.txt"
    source.write_text("hello patent", encoding="utf-8")

    assert load_source_text(source) == "hello patent"


def test_load_source_text_pdf_dispatches(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source = tmp_path / "sample.pdf"
    source.write_bytes(b"%PDF-1.7")

    def fake_extract(_path: Path) -> str:
        return "pdf text"

    monkeypatch.setattr("app.source_loader._extract_text_from_pdf", fake_extract)

    assert load_source_text(source) == "pdf text"


def test_load_source_text_unsupported_format(tmp_path: Path) -> None:
    source = tmp_path / "sample.docx"
    source.write_text("not supported", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported input format"):
        load_source_text(source)
