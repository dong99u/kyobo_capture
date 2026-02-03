"""Tests for PDF compilation module."""


def test_compile_single_image_creates_pdf(tmp_path, sample_image):
    """Compiling a single image should create a valid PDF."""
    from capture_pdf.pdf_compiler import PDFCompiler
    compiler = PDFCompiler()
    output_path = tmp_path / "output.pdf"
    compiler.compile([sample_image], output_path)
    assert output_path.exists()
    assert output_path.suffix == ".pdf"


def test_compile_multiple_images_creates_multipage_pdf(tmp_path, sample_images):
    """Compiling multiple images should create multi-page PDF."""
    from capture_pdf.pdf_compiler import PDFCompiler
    from PyPDF2 import PdfReader

    compiler = PDFCompiler()
    output_path = tmp_path / "output.pdf"
    compiler.compile(sample_images, output_path)

    reader = PdfReader(output_path)
    assert len(reader.pages) == len(sample_images)


def test_pdf_page_size_matches_image(tmp_path, sample_image):
    """PDF page dimensions should match source image."""
    from capture_pdf.pdf_compiler import PDFCompiler
    from PyPDF2 import PdfReader

    compiler = PDFCompiler()
    output_path = tmp_path / "output.pdf"
    compiler.compile([sample_image], output_path)

    reader = PdfReader(output_path)
    page = reader.pages[0]
    # Compare dimensions (allowing for DPI conversion - Pillow uses 72 DPI)
    assert abs(float(page.mediabox.width) - sample_image.width) < 10


def test_compile_from_files_creates_pdf(tmp_path, sample_image_paths):
    """Compiling from file paths should create valid PDF."""
    from capture_pdf.pdf_compiler import PDFCompiler

    compiler = PDFCompiler()
    output_path = tmp_path / "output.pdf"
    compiler.compile_from_files(sample_image_paths, output_path)
    assert output_path.exists()
