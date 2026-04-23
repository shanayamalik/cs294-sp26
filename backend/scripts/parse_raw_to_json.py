from __future__ import annotations

from pathlib import Path

from app.parser import parse_patent_text
from app.source_loader import SUPPORTED_EXTENSIONS, load_source_text
from app.store import DocumentStore

BACKEND_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = BACKEND_ROOT / "data" / "raw"
PARSED_DIR = BACKEND_ROOT / "data" / "parsed"


def filename_to_id(file_name: str) -> str:
    lowered = Path(file_name).stem.lower()
    normalized = "".join(ch if ch.isalnum() else "-" for ch in lowered)
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    return normalized.strip("-")


def main() -> None:
    files = sorted(
        file_path
        for file_path in RAW_DIR.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not files:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        print(f"No supported files ({supported}) found in {RAW_DIR}")
        return

    store = DocumentStore()
    wrote_count = 0
    failed_count = 0

    for file_path in files:
        try:
            raw_text = load_source_text(file_path)
            doc_id = filename_to_id(file_path.name)
            document = parse_patent_text(doc_id=doc_id, source_file=file_path.name, raw_text=raw_text)
            out_path = store.write_document(PARSED_DIR, document)
            print(f"Wrote {out_path}")
            wrote_count += 1
        except ValueError as error:
            print(f"Skipped {file_path.name}: {error}")
            failed_count += 1

    print(f"Done. Parsed: {wrote_count}, Skipped: {failed_count}")


if __name__ == "__main__":
    main()
