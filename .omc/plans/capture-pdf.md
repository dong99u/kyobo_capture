# Kyobo Library MacBook Capture Macro - Implementation Plan

## Context

### Original Request
Create a macro program to capture pages from the Kyobo Library MacBook app and compile them into PDF.

### Interview Summary
- **Platform**: macOS (MacBook)
- **Target App**: 교보도서관 (Kyobo Library)
- **Technology Choice**: Python + PyObjC (flexible, good for complex logic, cross-platform testing possible)
- **Output Format**: PDF

### Research Findings
- NEM-NE/ebook-script uses AppleScript + Shell scripts + ImageMagick
- ParkGiraffe/Ebook-capture-macro-py uses Python + PyQt5 + pynput + Pillow
- Both approaches use OS-level screenshot to bypass app-level copy protection

---

## Work Objectives

### Core Objective
Build a Python-based CLI tool that automates page capture from Kyobo Library app and compiles captures into a single PDF.

### Deliverables
1. `capture_pdf/` - Main Python package
2. `capture_pdf/capturer.py` - Screen capture module
3. `capture_pdf/navigator.py` - Page navigation automation module
4. `capture_pdf/pdf_compiler.py` - PDF compilation module
5. `capture_pdf/cli.py` - Command-line interface
6. `tests/` - Comprehensive test suite following TDD
7. `README.md` - Usage documentation

### Definition of Done
- [ ] All tests pass (unit + integration)
- [ ] CLI can capture a specified number of pages from Kyobo Library app
- [ ] Output PDF contains all captured pages in correct order
- [ ] Works on macOS 12+ (Monterey and later)
- [ ] Clean code with no linter warnings

---

## Guardrails

### Must Have
- TDD approach: Write failing test first, then implement
- Separate structural and behavioral commits
- macOS screen capture using native APIs (PyObjC/Quartz)
- Keyboard simulation for page navigation
- Error handling for app not found/not focused
- Progress indicator during capture
- Configurable capture region and delay

### Must NOT Have
- GUI application (CLI only for v1)
- Windows/Linux support (macOS only)
- OCR or text extraction (pure image capture)
- Cloud storage integration
- Automatic book detection (manual region selection)

---

## Task Flow

```
[Phase 1: Project Setup]
    |
    v
[Phase 2: Core Capture Module]
    |
    v
[Phase 3: Navigation Module]
    |
    v
[Phase 4: PDF Compilation Module]
    |
    v
[Phase 5: CLI Integration]
    |
    v
[Phase 6: Integration Testing]
```

---

## Detailed TODOs

### Phase 1: Project Setup

#### Task 1.1: Initialize Python Project Structure
**Files**: `pyproject.toml`, `capture_pdf/__init__.py`, `tests/__init__.py`
**Acceptance Criteria**:
- [ ] Project uses modern Python packaging (pyproject.toml)
- [ ] pytest configured as test runner
- [ ] Dependencies declared: PyObjC, Pillow, reportlab, click

```bash
# Verification
python -c "import capture_pdf" && pytest --collect-only
```

#### Task 1.2: Create Test Fixtures
**File**: `tests/conftest.py`

```python
import pytest
from PIL import Image
from pathlib import Path


@pytest.fixture
def sample_image() -> Image.Image:
    """Create a sample test image."""
    return Image.new('RGB', (800, 1000), color='white')


@pytest.fixture
def sample_images() -> list[Image.Image]:
    """Create multiple sample test images with different colors."""
    colors = ['white', 'lightgray', 'lightblue']
    return [Image.new('RGB', (800, 1000), color=c) for c in colors]


@pytest.fixture
def sample_image_path(tmp_path: Path, sample_image: Image.Image) -> Path:
    """Create a sample image file on disk."""
    path = tmp_path / "sample.png"
    sample_image.save(path)
    return path


@pytest.fixture
def sample_image_paths(tmp_path: Path, sample_images: list[Image.Image]) -> list[Path]:
    """Create multiple sample image files on disk."""
    paths = []
    for i, img in enumerate(sample_images):
        path = tmp_path / f"sample_{i}.png"
        img.save(path)
        paths.append(path)
    return paths
```

**Acceptance Criteria**:
- [ ] Fixtures available for all test modules
- [ ] Images created with consistent dimensions (800x1000)

---

### Phase 2: Core Capture Module (TDD)

#### Task 2.0: Permission Check Implementation
**File**: `capture_pdf/permissions.py`
**Purpose**: Check and report macOS permissions before capture operations

```python
from Quartz import CGPreflightScreenCaptureAccess, CGRequestScreenCaptureAccess

def check_screen_recording_permission() -> bool:
    """
    Check if screen recording permission is granted.

    Returns:
        True if permission is granted, False otherwise.

    Note:
        - CGPreflightScreenCaptureAccess() is available on macOS 10.15+
        - Returns True if permission already granted
        - Returns False if permission denied or not yet requested
    """
    return CGPreflightScreenCaptureAccess()

def request_screen_recording_permission() -> bool:
    """
    Request screen recording permission from user.

    Returns:
        True if permission granted, False otherwise.

    Note:
        - On first call, shows system permission dialog
        - On subsequent calls, returns cached permission state
        - User must manually grant in System Preferences if denied
    """
    return CGRequestScreenCaptureAccess()

def check_accessibility_permission() -> bool:
    """
    Check if accessibility permission is granted (required for keyboard simulation).

    Returns:
        True if permission is granted, False otherwise.
    """
    from ApplicationServices import AXIsProcessTrusted
    return AXIsProcessTrusted()
```

**Test**: `tests/test_permissions.py`
```python
def test_permission_check_returns_bool():
    """Permission check should return boolean."""
    from capture_pdf.permissions import check_screen_recording_permission
    result = check_screen_recording_permission()
    assert isinstance(result, bool)

def test_accessibility_check_returns_bool():
    """Accessibility check should return boolean."""
    from capture_pdf.permissions import check_accessibility_permission
    result = check_accessibility_permission()
    assert isinstance(result, bool)
```

**Acceptance Criteria**:
- [ ] Permission check functions implemented
- [ ] Tests pass on macOS 10.15+
- [ ] Clear error messages when permissions denied

---

#### Task 2.1: Test - Capture Returns Image Data
**File**: `tests/test_capturer.py`
**Test**: `test_capture_screen_returns_pil_image`
```python
def test_capture_screen_returns_pil_image():
    """Capturing screen should return a PIL Image object."""
    capturer = ScreenCapturer()
    image = capturer.capture_full_screen()
    assert isinstance(image, Image.Image)
    assert image.width > 0
    assert image.height > 0
```
**Acceptance Criteria**:
- [ ] Test written and fails (Red)
- [ ] Minimal implementation passes test (Green)

#### Task 2.2: Test - Capture Region
**File**: `tests/test_capturer.py`
**Test**: `test_capture_region_returns_cropped_image`
```python
def test_capture_region_returns_cropped_image():
    """Capturing a region should return image of specified size."""
    capturer = ScreenCapturer()
    region = CaptureRegion(x=100, y=100, width=200, height=300)
    image = capturer.capture_region(region)
    assert image.width == 200
    assert image.height == 300
```
**Acceptance Criteria**:
- [ ] Test written and fails (Red)
- [ ] Implementation using Quartz CGWindowListCreateImage (Green)

#### Task 2.3: Test - Save Capture to File
**File**: `tests/test_capturer.py`
**Test**: `test_save_capture_creates_png_file`
```python
def test_save_capture_creates_png_file(tmp_path):
    """Saving capture should create a PNG file on disk."""
    capturer = ScreenCapturer()
    image = capturer.capture_full_screen()
    output_path = tmp_path / "capture.png"
    capturer.save(image, output_path)
    assert output_path.exists()
    assert output_path.stat().st_size > 0
```
**Acceptance Criteria**:
- [ ] Test passes with Pillow save functionality

#### Task 2.4: Implement ScreenCapturer Class
**File**: `capture_pdf/capturer.py`

**Critical Implementation: CGImage to PIL Image Conversion**

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image
from Quartz import (
    CGWindowListCreateImage,
    CGRectMake,
    CGRectInfinite,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID,
    CGImageGetWidth,
    CGImageGetHeight,
    CGImageGetBytesPerRow,
    CGImageGetDataProvider,
    CGDataProviderCopyData,
)
from CoreFoundation import CFDataGetBytes, CFDataGetLength
import numpy as np


@dataclass
class CaptureRegion:
    """
    Capture region in PIXEL coordinates (not points).

    Note on Retina displays:
        - Coordinates are in pixels, not points
        - A 100x100 point region on a 2x Retina display = 200x200 pixels
        - Use NSScreen.backingScaleFactor to convert points to pixels if needed
        - Example: pixel_x = point_x * backingScaleFactor
    """
    x: int
    y: int
    width: int
    height: int


def cg_image_to_pil(cg_image) -> Image.Image:
    """
    Convert a Quartz CGImage to a PIL Image.

    Args:
        cg_image: A CGImageRef from CGWindowListCreateImage or similar

    Returns:
        PIL.Image.Image in RGBA mode

    Implementation Notes:
        - CGImage stores pixels in BGRA format (on most systems)
        - We need to convert to RGBA for PIL compatibility
        - Uses numpy for efficient byte manipulation
    """
    width = CGImageGetWidth(cg_image)
    height = CGImageGetHeight(cg_image)
    bytes_per_row = CGImageGetBytesPerRow(cg_image)

    # Get raw pixel data
    data_provider = CGImageGetDataProvider(cg_image)
    cf_data = CGDataProviderCopyData(data_provider)
    data_length = CFDataGetLength(cf_data)

    # Create buffer and copy data
    buffer = bytearray(data_length)
    CFDataGetBytes(cf_data, (0, data_length), buffer)

    # Convert to numpy array
    # Note: bytes_per_row may include padding, so we need to handle it
    arr = np.frombuffer(buffer, dtype=np.uint8)
    arr = arr.reshape((height, bytes_per_row // 4, 4))
    arr = arr[:, :width, :]  # Remove any padding

    # Convert BGRA to RGBA
    arr = arr[:, :, [2, 1, 0, 3]]

    # Create PIL Image
    return Image.fromarray(arr, mode='RGBA')


class ScreenCapturer:
    """Screen capture using macOS Quartz APIs."""

    def __init__(self, scale_factor: float = 1.0):
        """
        Initialize capturer.

        Args:
            scale_factor: Display scale factor (2.0 for Retina displays).
                          Use NSScreen.mainScreen().backingScaleFactor() to get this value.
        """
        self.scale_factor = scale_factor

    def capture_full_screen(self) -> Image.Image:
        """Capture the entire screen."""
        cg_image = CGWindowListCreateImage(
            CGRectInfinite,
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID,
            0  # kCGWindowImageDefault
        )
        if cg_image is None:
            raise RuntimeError(
                "Screen capture failed. Please ensure Screen Recording permission is granted "
                "in System Preferences > Privacy & Security > Screen Recording"
            )
        return cg_image_to_pil(cg_image)

    def capture_region(self, region: CaptureRegion) -> Image.Image:
        """
        Capture a specific region of the screen.

        Args:
            region: CaptureRegion with pixel coordinates (not points)

        Returns:
            PIL Image of the captured region
        """
        rect = CGRectMake(region.x, region.y, region.width, region.height)
        cg_image = CGWindowListCreateImage(
            rect,
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID,
            0  # kCGWindowImageDefault
        )
        if cg_image is None:
            raise RuntimeError(
                "Region capture failed. Check Screen Recording permission."
            )
        return cg_image_to_pil(cg_image)

    def save(self, image: Image.Image, path: Path) -> None:
        """Save image to file."""
        image.save(path)
```

**Retina Display Handling Note**:
- All region coordinates in `CaptureRegion` are in **pixels**, not points
- On a 2x Retina display, a 200x200 pixel region is 100x100 points
- To capture a region at a specific point location, multiply by scale factor:
  ```python
  from AppKit import NSScreen
  scale = NSScreen.mainScreen().backingScaleFactor()
  pixel_x = int(point_x * scale)
  pixel_y = int(point_y * scale)
  ```

**Acceptance Criteria**:
- [ ] All Task 2.x tests pass
- [ ] Uses Quartz (PyObjC) for native macOS capture
- [ ] CGImage to PIL conversion works correctly
- [ ] Handles Retina display scaling

---

### Phase 3: Navigation Module (TDD)

#### Task 3.1: Test - Simulate Key Press
**File**: `tests/test_navigator.py`
**Test**: `test_simulate_key_press_does_not_raise`
```python
def test_simulate_key_press_does_not_raise():
    """Simulating a key press should complete without error."""
    navigator = PageNavigator()
    # Should not raise exception
    navigator.press_key(KeyCode.RIGHT_ARROW)
```
**Acceptance Criteria**:
- [ ] Test written and fails (Red)
- [ ] Implementation using Quartz CGEventCreateKeyboardEvent (Green)

#### Task 3.2: Test - Navigate Next Page
**File**: `tests/test_navigator.py`
**Test**: `test_next_page_sends_right_arrow_or_click`
```python
def test_next_page_sends_right_arrow():
    """Next page should send right arrow key."""
    navigator = PageNavigator()
    with patch.object(navigator, 'press_key') as mock_press:
        navigator.next_page()
        mock_press.assert_called_once_with(KeyCode.RIGHT_ARROW)
```
**Acceptance Criteria**:
- [ ] Test written and fails (Red)
- [ ] Implementation sends right arrow key (Green)

#### Task 3.3: Test - Wait for Page Load
**File**: `tests/test_navigator.py`
**Test**: `test_wait_for_page_respects_delay`
```python
def test_wait_for_page_respects_delay():
    """Wait should pause for specified duration."""
    navigator = PageNavigator(page_delay=0.5)
    start = time.time()
    navigator.wait_for_page()
    elapsed = time.time() - start
    assert elapsed >= 0.5
```
**Acceptance Criteria**:
- [ ] Test passes with configurable delay

#### Task 3.4: Implement PageNavigator Class
**File**: `capture_pdf/navigator.py`

**Complete Keyboard Event Posting Implementation**:

```python
import time
from enum import IntEnum
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventPost,
    CGEventSetFlags,
    kCGHIDEventTap,
    kCGEventFlagMaskShift,
    kCGEventFlagMaskCommand,
)


class KeyCode(IntEnum):
    """
    macOS virtual key codes.
    Reference: https://developer.apple.com/documentation/coregraphics/cgeventflags
    """
    # Arrow keys
    RIGHT_ARROW = 0x7C
    LEFT_ARROW = 0x7B
    UP_ARROW = 0x7E
    DOWN_ARROW = 0x7D

    # Common keys
    RETURN = 0x24
    TAB = 0x30
    SPACE = 0x31
    DELETE = 0x33
    ESCAPE = 0x35

    # Function keys
    F1 = 0x7A
    F2 = 0x78
    F3 = 0x63
    F4 = 0x76
    F5 = 0x60

    # Letter keys (for potential shortcuts)
    KEY_A = 0x00
    KEY_S = 0x01
    KEY_D = 0x02
    KEY_F = 0x03
    KEY_N = 0x2D
    KEY_P = 0x23

    # Number keys
    KEY_0 = 0x1D
    KEY_1 = 0x12
    KEY_2 = 0x13
    KEY_3 = 0x14

    # Page navigation (some apps use these)
    PAGE_UP = 0x74
    PAGE_DOWN = 0x79
    HOME = 0x73
    END = 0x77


class PageNavigator:
    """
    Page navigation using macOS Quartz keyboard simulation.

    Requires Accessibility permission in System Preferences.
    """

    def __init__(self, page_delay: float = 1.0):
        """
        Initialize navigator.

        Args:
            page_delay: Seconds to wait after page navigation for content to load
        """
        self.page_delay = page_delay

    def press_key(self, key_code: KeyCode, modifiers: int = 0) -> None:
        """
        Simulate a key press (down + up).

        Args:
            key_code: The virtual key code to press
            modifiers: Optional modifier flags (kCGEventFlagMaskShift, kCGEventFlagMaskCommand, etc.)

        Implementation:
            1. Create key-down event
            2. Optionally set modifier flags
            3. Post key-down event to HID event tap
            4. Create key-up event
            5. Post key-up event
            6. Small delay for system to process

        Raises:
            RuntimeError: If event creation fails (usually permission issue)
        """
        # Key down event
        event_down = CGEventCreateKeyboardEvent(None, key_code, True)
        if event_down is None:
            raise RuntimeError(
                "Failed to create keyboard event. "
                "Please grant Accessibility permission in "
                "System Preferences > Privacy & Security > Accessibility"
            )

        if modifiers:
            CGEventSetFlags(event_down, modifiers)

        CGEventPost(kCGHIDEventTap, event_down)

        # Small delay between down and up
        time.sleep(0.05)

        # Key up event
        event_up = CGEventCreateKeyboardEvent(None, key_code, False)
        if modifiers:
            CGEventSetFlags(event_up, modifiers)

        CGEventPost(kCGHIDEventTap, event_up)

        # Allow system to process the event
        time.sleep(0.05)

    def press_key_with_command(self, key_code: KeyCode) -> None:
        """Press a key with Command modifier (e.g., Cmd+Right for some apps)."""
        self.press_key(key_code, modifiers=kCGEventFlagMaskCommand)

    def next_page(self) -> None:
        """Navigate to next page using right arrow key."""
        self.press_key(KeyCode.RIGHT_ARROW)

    def previous_page(self) -> None:
        """Navigate to previous page using left arrow key."""
        self.press_key(KeyCode.LEFT_ARROW)

    def wait_for_page(self) -> None:
        """Wait for page content to load."""
        time.sleep(self.page_delay)

    def navigate_and_wait(self) -> None:
        """Navigate to next page and wait for it to load."""
        self.next_page()
        self.wait_for_page()
```

**Event Flow Diagram**:
```
press_key(RIGHT_ARROW)
    |
    v
CGEventCreateKeyboardEvent(None, 0x7C, True)  # Key down
    |
    v
CGEventPost(kCGHIDEventTap, event_down)       # Send to system
    |
    v
sleep(0.05)                                    # Brief pause
    |
    v
CGEventCreateKeyboardEvent(None, 0x7C, False) # Key up
    |
    v
CGEventPost(kCGHIDEventTap, event_up)         # Send to system
```

**Acceptance Criteria**:
- [ ] All Task 3.x tests pass
- [ ] Uses Quartz CGEventPost for keyboard simulation
- [ ] Complete key press lifecycle (down + up)
- [ ] Supports modifier keys (Cmd, Shift, etc.)
- [ ] Handles permission errors gracefully

---

### Phase 4: PDF Compilation Module (TDD)

#### Task 4.1: Test - Create PDF from Single Image
**File**: `tests/test_pdf_compiler.py`
**Test**: `test_compile_single_image_creates_pdf`
```python
def test_compile_single_image_creates_pdf(tmp_path, sample_image):
    """Compiling a single image should create a valid PDF."""
    compiler = PDFCompiler()
    output_path = tmp_path / "output.pdf"
    compiler.compile([sample_image], output_path)
    assert output_path.exists()
    assert output_path.suffix == ".pdf"
```
**Acceptance Criteria**:
- [ ] Test written and fails (Red)
- [ ] Implementation using reportlab or Pillow PDF (Green)

#### Task 4.2: Test - Create PDF from Multiple Images
**File**: `tests/test_pdf_compiler.py`
**Test**: `test_compile_multiple_images_creates_multipage_pdf`
```python
def test_compile_multiple_images_creates_multipage_pdf(tmp_path, sample_images):
    """Compiling multiple images should create multi-page PDF."""
    compiler = PDFCompiler()
    output_path = tmp_path / "output.pdf"
    compiler.compile(sample_images, output_path)

    # Verify page count
    from PyPDF2 import PdfReader
    reader = PdfReader(output_path)
    assert len(reader.pages) == len(sample_images)
```
**Acceptance Criteria**:
- [ ] Test passes with multiple images
- [ ] Page order preserved

#### Task 4.3: Test - PDF Page Size Matches Image
**File**: `tests/test_pdf_compiler.py`
**Test**: `test_pdf_page_size_matches_image`
```python
def test_pdf_page_size_matches_image(tmp_path, sample_image):
    """PDF page dimensions should match source image."""
    compiler = PDFCompiler()
    output_path = tmp_path / "output.pdf"
    compiler.compile([sample_image], output_path)

    from PyPDF2 import PdfReader
    reader = PdfReader(output_path)
    page = reader.pages[0]
    # Compare dimensions (allowing for DPI conversion)
    assert abs(float(page.mediabox.width) - sample_image.width) < 10
```
**Acceptance Criteria**:
- [ ] PDF dimensions match source images

#### Task 4.4: Implement PDFCompiler Class
**File**: `capture_pdf/pdf_compiler.py`
```python
class PDFCompiler:
    def compile(self, images: List[Image.Image], output_path: Path) -> None: ...
    def compile_from_files(self, image_paths: List[Path], output_path: Path) -> None: ...
```
**Acceptance Criteria**:
- [ ] All Task 4.x tests pass
- [ ] Uses Pillow's PDF save capability

---

### Phase 5: CLI Integration (TDD)

#### Task 5.1: Test - CLI Parses Arguments
**File**: `tests/test_cli.py`
**Test**: `test_cli_requires_page_count`
```python
def test_cli_requires_page_count():
    """CLI should require --pages argument."""
    from click.testing import CliRunner
    from capture_pdf.cli import main

    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code != 0
    assert "pages" in result.output.lower()
```
**Acceptance Criteria**:
- [ ] CLI validates required arguments

#### Task 5.2: Test - CLI Capture Workflow
**File**: `tests/test_cli.py`
**Test**: `test_cli_captures_specified_pages`
```python
def test_cli_captures_specified_pages(tmp_path, mocker):
    """CLI should capture the specified number of pages."""
    mocker.patch('capture_pdf.cli.ScreenCapturer')
    mocker.patch('capture_pdf.cli.PageNavigator')
    mocker.patch('capture_pdf.cli.PDFCompiler')

    runner = CliRunner()
    output = tmp_path / "book.pdf"
    result = runner.invoke(main, ['--pages', '5', '--output', str(output)])

    assert result.exit_code == 0
```
**Acceptance Criteria**:
- [ ] CLI orchestrates capture workflow correctly

#### Task 5.3: Test - CLI Progress Output
**File**: `tests/test_cli.py`
**Test**: `test_cli_shows_progress`
```python
def test_cli_shows_progress(tmp_path, mocker):
    """CLI should show capture progress."""
    mocker.patch('capture_pdf.cli.ScreenCapturer')
    mocker.patch('capture_pdf.cli.PageNavigator')
    mocker.patch('capture_pdf.cli.PDFCompiler')

    runner = CliRunner()
    result = runner.invoke(main, ['--pages', '3', '--output', 'out.pdf'])

    assert "1/3" in result.output or "Page 1" in result.output
```
**Acceptance Criteria**:
- [ ] Progress indicator shows during capture

#### Task 5.4: Implement CLI
**File**: `capture_pdf/cli.py`
```python
import click

@click.command()
@click.option('--pages', '-p', required=True, type=int, help='Number of pages to capture')
@click.option('--output', '-o', required=True, type=click.Path(), help='Output PDF path')
@click.option('--delay', '-d', default=1.0, type=float, help='Delay between pages (seconds)')
@click.option('--region', '-r', type=str, help='Capture region as x,y,w,h')
def main(pages, output, delay, region):
    """Capture pages from Kyobo Library and compile to PDF."""
    ...
```
**Acceptance Criteria**:
- [ ] All Task 5.x tests pass
- [ ] CLI provides clear usage help

---

### Phase 6: Integration Testing

#### Task 6.1: Test - End-to-End Capture Simulation
**File**: `tests/test_integration.py`
**Test**: `test_full_capture_workflow`
```python
@pytest.mark.integration
def test_full_capture_workflow(tmp_path, mocker):
    """Full workflow: capture multiple pages and create PDF."""
    # Mock the actual screen capture for CI
    mock_image = Image.new('RGB', (800, 1000), color='white')
    mocker.patch.object(ScreenCapturer, 'capture_region', return_value=mock_image)
    mocker.patch.object(PageNavigator, 'press_key')

    from capture_pdf.cli import capture_book
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
```
**Acceptance Criteria**:
- [ ] Integration test passes
- [ ] Workflow produces valid PDF

#### Task 6.2: Manual Testing Checklist
**Acceptance Criteria**:
- [ ] Kyobo Library app can be targeted
- [ ] Capture region selection works
- [ ] Page navigation advances correctly
- [ ] Generated PDF is viewable and complete
- [ ] No errors during 10+ page capture

---

## Commit Strategy

| Phase | Commit Type | Message Format |
|-------|-------------|----------------|
| 1 | Structural | `chore: initialize project structure with pyproject.toml` |
| 2.1-2.3 | Behavioral | `test: add ScreenCapturer tests` |
| 2.4 | Behavioral | `feat: implement ScreenCapturer with Quartz` |
| 3.1-3.3 | Behavioral | `test: add PageNavigator tests` |
| 3.4 | Behavioral | `feat: implement PageNavigator with keyboard simulation` |
| 4.1-4.3 | Behavioral | `test: add PDFCompiler tests` |
| 4.4 | Behavioral | `feat: implement PDFCompiler` |
| 5.1-5.3 | Behavioral | `test: add CLI tests` |
| 5.4 | Behavioral | `feat: implement CLI with click` |
| 6 | Behavioral | `test: add integration tests` |

---

## Success Criteria

### Functional
- [ ] Capture 10+ pages from Kyobo Library app without errors
- [ ] Generated PDF opens in Preview and other PDF viewers
- [ ] Page quality matches screen resolution
- [ ] CLI provides clear feedback during operation

### Technical
- [ ] 90%+ test coverage for core modules
- [ ] Zero linter warnings (ruff/flake8)
- [ ] Type hints on all public functions
- [ ] Works on macOS 12+ (Monterey, Ventura, Sonoma)

### Performance
- [ ] Capture + navigate cycle < 3 seconds per page
- [ ] PDF compilation < 1 second for 100 pages
- [ ] Memory usage < 500MB for 100-page book

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Kyobo Library blocks screenshots | High | Use OS-level capture (CGWindowListCreateImage) which bypasses app-level protection |
| Accessibility permissions denied | High | Document permission setup in README; provide clear error message |
| Page navigation timing varies | Medium | Make delay configurable; add --delay flag |
| Screen resolution differences | Medium | Use relative positioning for region; document setup |
| macOS version incompatibility | Medium | Test on multiple macOS versions; use stable PyObjC APIs |

---

## Dependencies

```toml
[project]
dependencies = [
    "pyobjc-framework-Quartz>=10.0",
    "pyobjc-framework-ApplicationServices>=10.0",  # For AXIsProcessTrusted
    "pyobjc-framework-Cocoa>=10.0",  # For NSScreen, NSWorkspace
    "Pillow>=10.0",
    "numpy>=1.24",  # For CGImage to PIL conversion
    "click>=8.0",
    "PyPDF2>=3.0",  # For PDF verification in tests
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-mock>=3.0",
    "ruff>=0.1",
]
```

---

## Notes

### Permissions Required
- **Screen Recording Permission**: Required for screen capture. Grant in System Preferences > Privacy & Security > Screen Recording
- **Accessibility Permission**: Required for keyboard simulation. Grant in System Preferences > Privacy & Security > Accessibility

### Kyobo Library App
- **Bundle ID**: `com.kyobobook.Kyobo도서관` (may vary by version; verify with `osascript -e 'id of app "교보도서관"'`)
- **Alternative Bundle IDs**: Check `mdls -name kMDItemCFBundleIdentifier /Applications/교보도서관.app`
- Must be open and displaying the book before running capture
- App must be in foreground for keyboard events to work

### Coordinate System
- **v1 uses pixel coordinates** for capture regions (not points)
- On Retina displays, multiply point coordinates by `NSScreen.mainScreen().backingScaleFactor()`
- Future version could add interactive region selection

### Design Decisions (Architect Questions Resolved)

**Q: Should the capture module support window-specific capture or full-screen with region crop?**
- **Decision**: Full-screen capture with region crop (simpler, more reliable)
- **Rationale**: Window-specific capture requires window ID lookup and may fail if window is partially obscured. Region crop is more predictable and works regardless of window state.
- **Future Enhancement**: Could add window-specific mode via `--window` flag

**Q: Should the tool auto-refocus Kyobo Library if it loses focus?**
- **Decision**: No auto-refocus in v1 (configurable in future)
- **Rationale**: Auto-refocus can be disruptive. User should ensure app is focused before starting. Add `--require-focus` flag that validates focus before each capture.
- **Implementation Note**: Add a pre-capture check that warns if Kyobo Library is not the frontmost app:
  ```python
  from AppKit import NSWorkspace

  def is_kyobo_frontmost() -> bool:
      active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
      return "kyobo" in active_app.bundleIdentifier().lower()
  ```
