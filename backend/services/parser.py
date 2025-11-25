from pathlib import Path
import json
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    OcrAutoOptions,
    TableStructureOptions,
    TableFormerMode,
)
from docling.document_converter import DocumentConverter, PdfFormatOption

def parse_pdf(file_path: str):
    """
    Parses a PDF file using Docling and returns the DoclingDocument object.
    
    Args:
        file_path (str): The absolute path to the PDF file.
        
    Returns:
        DoclingDocument: The parsed document object (for chunking and graph extraction).
    """
    
    # Configure the pipeline options
    pipe = PdfPipelineOptions(
        do_ocr=True,
        ocr_options=OcrAutoOptions(),
        do_table_structure=True,
        table_structure_options=TableStructureOptions(
            mode=TableFormerMode.ACCURATE
        ),
    )

    # Initialize the converter
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipe)}
    )

    # Convert the document
    result = converter.convert(file_path)
    return result.document
