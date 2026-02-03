"""Integration tests for the full capture workflow."""
import pytest
from PIL import Image
from PyPDF2 import PdfReader

from capture_pdf.capturer import ScreenCapturer, CaptureRegion
from capture_pdf.navigator import PageNavigator
from capture_pdf.cli import capture_book


@pytest.mark.integration
def test_full_capture_workflow(tmp_path, mocker):
    """Full workflow: capture multiple pages and create PDF."""
    # Mock the actual screen capture for CI
    mock_image = Image.new('RGB', (800, 1000), color='white')
    mocker.patch.object(ScreenCapturer, 'capture_region', return_value=mock_image)
    mocker.patch.object(ScreenCapturer, 'capture_full_screen', return_value=mock_image)
    mocker.patch.object(PageNavigator, 'press_key')
    mocker.patch('capture_pdf.cli.check_screen_recording_permission', return_value=True)
    mocker.patch('capture_pdf.cli.check_accessibility_permission', return_value=True)

    output_path = tmp_path / "book.pdf"

    capture_book(
        page_count=3,
        output_path=output_path,
        region=CaptureRegion(0, 0, 800, 1000),
        delay=0.1
    )

    assert output_path.exists()
    reader = PdfReader(output_path)
    assert len(reader.pages) == 3


@pytest.mark.integration
def test_full_screen_capture_workflow(tmp_path, mocker):
    """Full workflow with full screen capture."""
    mock_image = Image.new('RGB', (1920, 1080), color='lightgray')
    mocker.patch.object(ScreenCapturer, 'capture_full_screen', return_value=mock_image)
    mocker.patch.object(PageNavigator, 'press_key')
    mocker.patch('capture_pdf.cli.check_screen_recording_permission', return_value=True)
    mocker.patch('capture_pdf.cli.check_accessibility_permission', return_value=True)

    output_path = tmp_path / "fullscreen_book.pdf"

    capture_book(
        page_count=5,
        output_path=output_path,
        region=None,  # Full screen
        delay=0.1
    )

    assert output_path.exists()
    reader = PdfReader(output_path)
    assert len(reader.pages) == 5


@pytest.mark.integration
def test_workflow_with_different_page_counts(tmp_path, mocker):
    """Test various page counts."""
    mock_image = Image.new('RGB', (600, 800), color='white')
    mocker.patch.object(ScreenCapturer, 'capture_region', return_value=mock_image)
    mocker.patch.object(PageNavigator, 'press_key')
    mocker.patch('capture_pdf.cli.check_screen_recording_permission', return_value=True)
    mocker.patch('capture_pdf.cli.check_accessibility_permission', return_value=True)

    for count in [1, 2, 10]:
        output_path = tmp_path / f"book_{count}.pdf"
        capture_book(
            page_count=count,
            output_path=output_path,
            region=CaptureRegion(0, 0, 600, 800),
            delay=0.01
        )
        reader = PdfReader(output_path)
        assert len(reader.pages) == count
