from pathlib import Path
import json
from docling_core.types.doc import ImageRefMode

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    OcrAutoOptions,
    TableStructureOptions,
    TableFormerMode,
)
from docling.document_converter import DocumentConverter, PdfFormatOption

# ----------------- input/output to test parser performance ---------------------
INPUT_PDF = "Data/Insurance/Sample Policy Specimen.pdf"
OUT_DIR = Path("results")
# --------------------------------------------------------------------------------

def parse_pdf(input_pdf: str):
    """
    Parse a PDF using Docling with OCR and table structure recognition.
    
    Args:
        input_pdf: Path to the PDF file to parse
        
    Returns:
        DoclingDocument: Parsed document object
    """
    pipe = PdfPipelineOptions(
        do_ocr=True,
        ocr_options=OcrAutoOptions(),
        do_table_structure=True,
        table_structure_options=TableStructureOptions(
            mode=TableFormerMode.ACCURATE
        ),
    )

    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipe)}
    )

    result = converter.convert(input_pdf)
    return result.document


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    doc = parse_pdf(INPUT_PDF)
    doc_filename = Path(INPUT_PDF).stem

    # Export Docling's native JSON format (contains all structured data)
    with (OUT_DIR / f"{doc_filename}.json").open("w", encoding="utf-8") as fp:
        fp.write(json.dumps(doc.export_to_dict(), indent=2))

    # Export Markdown format
    with (OUT_DIR / f"{doc_filename}.md").open("w", encoding="utf-8") as fp:
        fp.write(doc.export_to_markdown())

    print(f"Converted: {INPUT_PDF}")
    print(f"Saved: {doc_filename}.json, .md")

if __name__ == "__main__":
    main()
