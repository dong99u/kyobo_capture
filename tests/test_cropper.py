"""Tests for margin detection and page cropping module."""
from PIL import Image


def test_detect_black_margins_on_image_with_black_border():
    """Synthetic 100x100 white image with 10px black border should return inner box."""
    from capture_pdf.cropper import MarginDetector, CropBox

    # Create 100x100 white image with 10px black border
    img = Image.new('RGB', (100, 100), color='black')
    inner = Image.new('RGB', (80, 80), color='white')
    img.paste(inner, (10, 10))

    detector = MarginDetector(mode='black', threshold=10)
    box = detector.detect(img)

    assert box == CropBox(left=10, top=10, right=90, bottom=90)


def test_detect_no_margins_returns_full_image_bounds():
    """Image with no margins should return full image bounds."""
    from capture_pdf.cropper import MarginDetector, CropBox

    img = Image.new('RGB', (100, 80), color=(128, 128, 128))

    detector = MarginDetector(mode='black', threshold=10)
    box = detector.detect(img)

    assert box == CropBox(left=0, top=0, right=100, bottom=80)


def test_detect_asymmetric_margins():
    """Different margin widths per side should return correct asymmetric box."""
    from capture_pdf.cropper import MarginDetector, CropBox

    # 100x100 black image with asymmetric content:
    # top=5, bottom=15, left=20, right=10
    img = Image.new('RGB', (100, 100), color='black')
    content = Image.new('RGB', (70, 80), color='white')
    img.paste(content, (20, 5))  # left=20, top=5, right=90, bottom=85

    detector = MarginDetector(mode='black', threshold=10)
    box = detector.detect(img)

    assert box == CropBox(left=20, top=5, right=90, bottom=85)


def test_detect_white_margins_on_image_with_white_border():
    """Dark-content image with 10px white border should return correct inner box."""
    from capture_pdf.cropper import MarginDetector, CropBox

    # Create 100x100 dark image with 10px white border
    img = Image.new('RGB', (100, 100), color='white')
    inner = Image.new('RGB', (80, 80), color=(50, 50, 50))
    img.paste(inner, (10, 10))

    detector = MarginDetector(mode='white', threshold=10)
    box = detector.detect(img)

    assert box == CropBox(left=10, top=10, right=90, bottom=90)


def test_threshold_parameter_affects_detection():
    """Near-black pixels (RGB 5,5,5) should be treated as margin when threshold allows."""
    from capture_pdf.cropper import MarginDetector, CropBox

    # Create image with near-black border (5,5,5) instead of pure black
    img = Image.new('RGB', (100, 100), color=(5, 5, 5))
    inner = Image.new('RGB', (80, 80), color='white')
    img.paste(inner, (10, 10))

    # With threshold=10, near-black should be detected as margin
    detector = MarginDetector(mode='black', threshold=10)
    box = detector.detect(img)
    assert box == CropBox(left=10, top=10, right=90, bottom=90)

    # With threshold=0, near-black is NOT margin (strict matching)
    detector_strict = MarginDetector(mode='black', threshold=0)
    box_strict = detector_strict.detect(img)
    assert box_strict == CropBox(left=0, top=0, right=100, bottom=100)


def test_auto_detect_mode_identifies_margin_color():
    """Auto mode should sample 4 corner pixels and detect margin color."""
    from capture_pdf.cropper import MarginDetector, CropBox

    # Black border image - auto should detect black margins
    img_black = Image.new('RGB', (100, 100), color='black')
    inner_black = Image.new('RGB', (80, 80), color=(128, 128, 128))
    img_black.paste(inner_black, (10, 10))

    detector = MarginDetector(mode='auto', threshold=10)
    box = detector.detect(img_black)
    assert box == CropBox(left=10, top=10, right=90, bottom=90)

    # White border image - auto should detect white margins
    img_white = Image.new('RGB', (100, 100), color='white')
    inner_white = Image.new('RGB', (80, 80), color=(50, 50, 50))
    img_white.paste(inner_white, (10, 10))

    box_white = detector.detect(img_white)
    assert box_white == CropBox(left=10, top=10, right=90, bottom=90)


# --- Step 2: PageCropper tests ---


def _save_png_with_dpi(img, path, dpi=72):
    """Save PNG with explicit DPI metadata so img2pdf uses consistent sizing."""
    img.save(path, dpi=(dpi, dpi))


def _create_test_pdf_with_margins(tmp_path, page_count=1, margin=10, size=(100, 100)):
    """Helper: create a PDF with known margins using img2pdf."""
    import img2pdf

    image_paths = []
    for i in range(page_count):
        img = Image.new('RGB', size, color='black')
        content_w = size[0] - 2 * margin
        content_h = size[1] - 2 * margin
        content = Image.new('RGB', (content_w, content_h), color=(128, 128, 128))
        img.paste(content, (margin, margin))
        img_path = tmp_path / f"page_{i}.png"
        _save_png_with_dpi(img, img_path)
        image_paths.append(str(img_path))

    pdf_path = tmp_path / "input.pdf"
    with open(pdf_path, "wb") as f:
        f.write(img2pdf.convert(image_paths))
    return pdf_path


TEST_DPI = 72  # Use consistent DPI for crop and verification in tests


def test_crop_single_page_pdf(tmp_path):
    """Crop a 1-page PDF with 10px black margins; verify output dimensions."""
    from capture_pdf.cropper import MarginDetector, PageCropper

    pdf_path = _create_test_pdf_with_margins(tmp_path, page_count=1, margin=10, size=(100, 100))
    output_path = tmp_path / "output.pdf"

    detector = MarginDetector(mode='black', threshold=10)
    cropper = PageCropper(detector)
    cropper.crop_pdf(pdf_path, output_path, dpi=TEST_DPI)

    assert output_path.exists()
    from pdf2image import convert_from_path
    pages = convert_from_path(str(output_path), dpi=TEST_DPI)
    assert len(pages) == 1
    # Content is 80x80, so output should be approximately 80x80
    assert abs(pages[0].width - 80) <= 2
    assert abs(pages[0].height - 80) <= 2


def test_crop_multi_page_pdf(tmp_path):
    """3-page PDF with different margins; each page cropped independently."""
    import img2pdf

    image_paths = []
    margins = [10, 20, 5]
    for i, margin in enumerate(margins):
        img = Image.new('RGB', (100, 100), color='black')
        cw, ch = 100 - 2 * margin, 100 - 2 * margin
        content = Image.new('RGB', (cw, ch), color=(128, 128, 128))
        img.paste(content, (margin, margin))
        p = tmp_path / f"page_{i}.png"
        _save_png_with_dpi(img, p)
        image_paths.append(str(p))

    pdf_path = tmp_path / "multi.pdf"
    with open(pdf_path, "wb") as f:
        f.write(img2pdf.convert(image_paths))

    output_path = tmp_path / "output.pdf"

    from capture_pdf.cropper import MarginDetector, PageCropper
    detector = MarginDetector(mode='black', threshold=10)
    cropper = PageCropper(detector)
    cropper.crop_pdf(pdf_path, output_path, dpi=TEST_DPI)

    from pdf2image import convert_from_path
    pages = convert_from_path(str(output_path), dpi=TEST_DPI)
    assert len(pages) == 3


def test_padding_adds_pixels_after_crop(tmp_path):
    """Crop with padding=5; output dimensions should be content + 2*padding."""
    from capture_pdf.cropper import MarginDetector, PageCropper

    pdf_path = _create_test_pdf_with_margins(tmp_path, page_count=1, margin=10, size=(100, 100))
    output_path = tmp_path / "output.pdf"

    detector = MarginDetector(mode='black', threshold=10)
    cropper = PageCropper(detector, padding=5)
    cropper.crop_pdf(pdf_path, output_path, dpi=TEST_DPI)

    from pdf2image import convert_from_path
    pages = convert_from_path(str(output_path), dpi=TEST_DPI)
    # Content 80x80 + padding 5 on each side = 90x90
    assert abs(pages[0].width - 90) <= 2
    assert abs(pages[0].height - 90) <= 2


def test_crop_preserves_page_count(tmp_path):
    """Output PDF should have same number of pages as input."""
    from capture_pdf.cropper import MarginDetector, PageCropper

    pdf_path = _create_test_pdf_with_margins(tmp_path, page_count=5, margin=10, size=(100, 100))
    output_path = tmp_path / "output.pdf"

    detector = MarginDetector(mode='black', threshold=10)
    cropper = PageCropper(detector)
    cropper.crop_pdf(pdf_path, output_path, dpi=TEST_DPI)

    from pdf2image import convert_from_path
    pages = convert_from_path(str(output_path), dpi=TEST_DPI)
    assert len(pages) == 5


def test_crop_with_no_margins_produces_same_dimensions(tmp_path):
    """Input without margins should produce output with same page size."""
    import img2pdf

    img = Image.new('RGB', (100, 80), color=(128, 128, 128))
    img_path = tmp_path / "full.png"
    _save_png_with_dpi(img, img_path)

    pdf_path = tmp_path / "input.pdf"
    with open(pdf_path, "wb") as f:
        f.write(img2pdf.convert([str(img_path)]))

    output_path = tmp_path / "output.pdf"

    from capture_pdf.cropper import MarginDetector, PageCropper
    detector = MarginDetector(mode='black', threshold=10)
    cropper = PageCropper(detector)
    cropper.crop_pdf(pdf_path, output_path, dpi=TEST_DPI)

    from pdf2image import convert_from_path
    pages_in = convert_from_path(str(pdf_path), dpi=TEST_DPI)
    pages_out = convert_from_path(str(output_path), dpi=TEST_DPI)
    assert abs(pages_out[0].width - pages_in[0].width) <= 2
    assert abs(pages_out[0].height - pages_in[0].height) <= 2


# --- Step 3: CLI crop command tests ---


def test_crop_command_exists_in_cli():
    """crop command should appear in CLI help."""
    from click.testing import CliRunner
    from capture_pdf.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert 'crop' in result.output


def test_crop_requires_input_and_output():
    """Missing --input or --output should produce error."""
    from click.testing import CliRunner
    from capture_pdf.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ['crop'])
    assert result.exit_code != 0


def test_crop_processes_pdf_file(tmp_path):
    """crop command should process a PDF file end-to-end."""
    from click.testing import CliRunner
    from capture_pdf.cli import cli

    pdf_path = _create_test_pdf_with_margins(tmp_path, page_count=1, margin=10, size=(100, 100))
    output_path = tmp_path / "output.pdf"

    runner = CliRunner()
    result = runner.invoke(cli, ['crop', '-i', str(pdf_path), '-o', str(output_path)])

    assert result.exit_code == 0, f"CLI failed: {result.output}"
    assert output_path.exists()


def test_crop_passes_options_to_cropper(tmp_path):
    """mode, threshold, padding options should be forwarded to cropper."""
    from click.testing import CliRunner
    from capture_pdf.cli import cli

    pdf_path = _create_test_pdf_with_margins(tmp_path, page_count=1, margin=10, size=(100, 100))
    output_path = tmp_path / "output.pdf"

    runner = CliRunner()
    result = runner.invoke(cli, [
        'crop', '-i', str(pdf_path), '-o', str(output_path),
        '--mode', 'black', '--threshold', '15', '--padding', '5',
    ])

    assert result.exit_code == 0, f"CLI failed: {result.output}"
    assert output_path.exists()


# --- Step 4: Edge cases and integration ---


def test_crop_empty_pdf_raises_error(tmp_path):
    """PDF with 0 pages should raise ValueError."""
    import pytest
    from capture_pdf.cropper import MarginDetector, PageCropper

    # Create a minimal empty PDF (just header)
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

    output_path = tmp_path / "output.pdf"

    detector = MarginDetector(mode='black', threshold=10)
    cropper = PageCropper(detector)

    with pytest.raises(Exception):
        cropper.crop_pdf(pdf_path, output_path)


def test_crop_single_color_page_returns_minimal_box():
    """All-black or all-white page should be handled gracefully."""
    from capture_pdf.cropper import MarginDetector, CropBox

    # All-black image: every pixel is margin, so returns full bounds (no content found)
    img = Image.new('RGB', (100, 100), color='black')
    detector = MarginDetector(mode='black', threshold=10)
    box = detector.detect(img)
    # When everything is margin, scan returns 0 for top/left and full for bottom/right
    assert box.left == 0 and box.top == 0
    assert box.right == 100 and box.bottom == 100


def test_crop_integration_end_to_end(tmp_path):
    """Create images -> compile to PDF via img2pdf -> crop -> verify dimensions."""
    import img2pdf
    from capture_pdf.cropper import MarginDetector, PageCropper
    from pdf2image import convert_from_path

    # Create image with known 15px black margins
    img = Image.new('RGB', (200, 300), color='black')
    content = Image.new('RGB', (170, 270), color=(100, 150, 200))
    img.paste(content, (15, 15))
    img_path = tmp_path / "page.png"
    _save_png_with_dpi(img, img_path)

    # Compile to PDF (same as real workflow)
    pdf_path = tmp_path / "book.pdf"
    with open(pdf_path, "wb") as f:
        f.write(img2pdf.convert([str(img_path)]))

    # Crop
    output_path = tmp_path / "cropped.pdf"
    detector = MarginDetector(mode='auto', threshold=10)
    cropper = PageCropper(detector)
    cropper.crop_pdf(pdf_path, output_path, dpi=TEST_DPI)

    # Verify: output should be ~170x270
    pages = convert_from_path(str(output_path), dpi=TEST_DPI)
    assert len(pages) == 1
    assert abs(pages[0].width - 170) <= 2
    assert abs(pages[0].height - 270) <= 2
