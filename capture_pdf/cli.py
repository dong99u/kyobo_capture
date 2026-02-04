"""Command-line interface for capture_pdf."""
import sys
from pathlib import Path
from typing import Optional

import click

from capture_pdf.capturer import ScreenCapturer, CaptureRegion
from capture_pdf.navigator import PageNavigator
from capture_pdf.pdf_compiler import PDFCompiler
from capture_pdf.permissions import (
    check_screen_recording_permission,
    check_accessibility_permission,
)


def parse_region(region_str: Optional[str]) -> Optional[CaptureRegion]:
    """Parse region string 'x,y,w,h' into CaptureRegion."""
    if not region_str:
        return None
    try:
        parts = [int(x.strip()) for x in region_str.split(',')]
        if len(parts) != 4:
            raise ValueError("Region must have 4 values: x,y,width,height")
        return CaptureRegion(x=parts[0], y=parts[1], width=parts[2], height=parts[3])
    except ValueError as e:
        raise click.BadParameter(f"Invalid region format: {e}")


def parse_point(point_str: Optional[str]) -> Optional[tuple[int, int]]:
    """Parse point string 'x,y' into tuple."""
    if not point_str:
        return None
    try:
        parts = [int(x.strip()) for x in point_str.split(',')]
        if len(parts) != 2:
            raise ValueError("Point must have 2 values: x,y")
        return (parts[0], parts[1])
    except ValueError as e:
        raise click.BadParameter(f"Invalid point format: {e}")


def capture_book(
    page_count: int,
    output_path: Path,
    region: Optional[CaptureRegion] = None,
    delay: float = 1.0,
) -> None:
    """
    Capture pages directly and compile to PDF.
    """
    capturer = ScreenCapturer()
    navigator = PageNavigator(page_delay=delay)
    compiler = PDFCompiler()

    images = []
    try:
        for i in range(page_count):
            click.echo(f"Capturing page {i + 1}/{page_count}...")

            if region:
                image = capturer.capture_region(region)
            else:
                image = capturer.capture_full_screen()

            images.append(image)

            if i < page_count - 1:
                navigator.navigate_and_wait()

        click.echo(f"Compiling PDF to {output_path}...")
        compiler.compile(images, output_path)
        click.echo(f"Done! Created {output_path}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def capture_with_button(
    page_count: int,
    capture_button: tuple[int, int],
    output_folder: Path,
    delay: float = 1.0,
    capture_delay: float = 0.5,
    confirm_button: tuple[int, int] | None = None,
    confirm_delay: float = 0.3,
) -> None:
    """
    Capture pages by clicking app's capture button.

    Args:
        page_count: Number of pages to capture
        capture_button: (x, y) coordinates of the capture button
        output_folder: Folder where app saves captures
        delay: Delay between page turns
        capture_delay: Delay after clicking capture button
        confirm_button: Optional (x, y) coordinates of confirm/OK button for dialogs
        confirm_delay: Delay after clicking confirm button
    """
    navigator = PageNavigator(page_delay=delay)

    try:
        click.echo(f"Starting capture of {page_count} pages...")
        click.echo(f"Capture button at: ({capture_button[0]}, {capture_button[1]})")
        if confirm_button:
            click.echo(f"Confirm button at: ({confirm_button[0]}, {confirm_button[1]})")
        click.echo(f"Make sure Kyobo Library app is focused!")
        click.echo()

        # Give user time to focus the app
        click.echo("Starting in 3 seconds...")
        import time
        time.sleep(3)

        for i in range(page_count):
            click.echo(f"Page {i + 1}/{page_count}: Clicking capture button...")

            # Click capture button
            navigator.click_and_wait(capture_button[0], capture_button[1], capture_delay)

            # Click confirm button if specified (to dismiss warning dialog)
            if confirm_button:
                navigator.click_and_wait(confirm_button[0], confirm_button[1], confirm_delay)

            # Navigate to next page (except for last page)
            if i < page_count - 1:
                click.echo(f"Page {i + 1}/{page_count}: Navigating to next page...")
                navigator.navigate_and_wait()

        click.echo()
        click.echo(f"Done! Captured {page_count} pages.")
        click.echo(f"Check your capture folder for the saved images.")
        click.echo(f"You can use 'capture-pdf compile' to combine them into PDF.")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.group()
def cli():
    """Kyobo Library capture macro - capture pages and compile to PDF."""
    pass


@cli.command()
@click.option('--pages', '-p', required=True, type=int, help='Number of pages to capture')
@click.option('--output', '-o', required=True, type=click.Path(), help='Output PDF path')
@click.option('--delay', '-d', default=1.0, type=float, help='Delay between pages (seconds)')
@click.option('--region', '-r', type=str, help='Capture region as x,y,width,height')
def screenshot(pages: int, output: str, delay: float, region: Optional[str]) -> None:
    """Capture pages using direct screenshots."""
    if not check_screen_recording_permission():
        click.echo(
            "Error: Screen Recording permission not granted.\n"
            "Please grant permission in System Preferences > Privacy & Security > Screen Recording",
            err=True
        )
        sys.exit(1)

    if not check_accessibility_permission():
        click.echo(
            "Error: Accessibility permission not granted.\n"
            "Please grant permission in System Preferences > Privacy & Security > Accessibility",
            err=True
        )
        sys.exit(1)

    capture_region = parse_region(region)
    output_path = Path(output)
    capture_book(
        page_count=pages,
        output_path=output_path,
        region=capture_region,
        delay=delay,
    )


@cli.command()
@click.option('--pages', '-p', required=True, type=int, help='Number of pages to capture')
@click.option('--button', '-b', required=True, type=str, help='Capture button position as x,y')
@click.option('--confirm', type=str, help='Confirm button position as x,y (for dismissing dialogs)')
@click.option('--delay', '-d', default=1.0, type=float, help='Delay between pages (seconds)')
@click.option('--capture-delay', '-c', default=0.5, type=float, help='Delay after clicking capture (seconds)')
def button(pages: int, button: str, confirm: str, delay: float, capture_delay: float) -> None:
    """Capture pages by clicking the app's capture button."""
    if not check_accessibility_permission():
        click.echo(
            "Error: Accessibility permission not granted.\n"
            "Please grant permission in System Preferences > Privacy & Security > Accessibility",
            err=True
        )
        sys.exit(1)

    capture_button = parse_point(button)
    if not capture_button:
        click.echo("Error: --button is required", err=True)
        sys.exit(1)

    confirm_button = parse_point(confirm) if confirm else None

    capture_with_button(
        page_count=pages,
        capture_button=capture_button,
        output_folder=Path("."),
        delay=delay,
        capture_delay=capture_delay,
        confirm_button=confirm_button,
    )


@cli.command()
@click.option('--input', '-i', required=True, type=click.Path(exists=True), help='Folder with captured images')
@click.option('--output', '-o', required=True, type=click.Path(), help='Output PDF path')
@click.option('--pattern', default='*.png', help='File pattern to match (default: *.png)')
@click.option('--sort', type=click.Choice(['name', 'time', 'time-desc']), default='name', help='Sort: name, time (oldest first), time-desc (newest first)')
def compile(input: str, output: str, pattern: str, sort: str) -> None:
    """Compile captured images into PDF (lossless, original quality)."""
    from pathlib import Path
    import os
    import img2pdf

    input_path = Path(input)
    output_path = Path(output)

    # Find all matching images
    image_files = list(input_path.glob(pattern))

    if not image_files:
        click.echo(f"No images found matching '{pattern}' in {input_path}", err=True)
        sys.exit(1)

    # Sort files
    if sort == 'time':
        # Sort by modification time (oldest first)
        image_files.sort(key=lambda f: os.path.getmtime(f))
        click.echo(f"Sorting by creation time (oldest first)")
    elif sort == 'time-desc':
        # Sort by modification time (newest first)
        image_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        click.echo(f"Sorting by creation time (newest first)")
    else:
        image_files.sort()
        click.echo(f"Sorting by filename")

    click.echo(f"Found {len(image_files)} images")
    click.echo(f"Converting with original quality (lossless)...")

    # Use img2pdf for lossless conversion
    with open(output_path, "wb") as f:
        f.write(img2pdf.convert([str(p) for p in image_files]))

    click.echo(f"Created {output_path}")


# Keep legacy main() for backwards compatibility
def main(pages: int = None, output: str = None, delay: float = 1.0, region: str = None):
    """Legacy entry point - redirects to screenshot command."""
    if pages is None or output is None:
        cli()
    else:
        if not check_screen_recording_permission():
            click.echo("Error: Screen Recording permission not granted.", err=True)
            sys.exit(1)
        if not check_accessibility_permission():
            click.echo("Error: Accessibility permission not granted.", err=True)
            sys.exit(1)
        capture_region = parse_region(region)
        capture_book(pages, Path(output), capture_region, delay)


if __name__ == '__main__':
    cli()
