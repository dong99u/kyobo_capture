"""Tests for screen capture module."""
from PIL import Image


def test_capture_screen_returns_pil_image():
    """Capturing screen should return a PIL Image object."""
    from capture_pdf.capturer import ScreenCapturer
    capturer = ScreenCapturer()
    image = capturer.capture_full_screen()
    assert isinstance(image, Image.Image)
    assert image.width > 0
    assert image.height > 0


def test_capture_region_returns_cropped_image():
    """Capturing a region should return image of specified size."""
    from capture_pdf.capturer import ScreenCapturer, CaptureRegion
    capturer = ScreenCapturer()
    region = CaptureRegion(x=100, y=100, width=200, height=300)
    image = capturer.capture_region(region)
    assert image.width == 200
    assert image.height == 300


def test_save_capture_creates_png_file(tmp_path):
    """Saving capture should create a PNG file on disk."""
    from capture_pdf.capturer import ScreenCapturer
    capturer = ScreenCapturer()
    image = capturer.capture_full_screen()
    output_path = tmp_path / "capture.png"
    capturer.save(image, output_path)
    assert output_path.exists()
    assert output_path.stat().st_size > 0
