"""Tests for CLI interface."""
from click.testing import CliRunner


def test_cli_requires_page_count():
    """CLI should require --pages argument."""
    from capture_pdf.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ['screenshot'])
    assert result.exit_code != 0
    assert "pages" in result.output.lower() or "missing" in result.output.lower()


def test_cli_requires_output():
    """CLI should require --output argument."""
    from capture_pdf.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ['screenshot', '--pages', '5'])
    assert result.exit_code != 0
    assert "output" in result.output.lower() or "missing" in result.output.lower()


def test_cli_captures_specified_pages(tmp_path, mocker):
    """CLI should capture the specified number of pages."""
    from capture_pdf.cli import cli
    from PIL import Image

    mock_image = Image.new('RGB', (800, 1000), color='white')
    mock_capturer = mocker.patch('capture_pdf.cli.ScreenCapturer')
    mock_capturer.return_value.capture_region.return_value = mock_image
    mock_capturer.return_value.capture_full_screen.return_value = mock_image

    mocker.patch('capture_pdf.cli.PageNavigator')
    mocker.patch('capture_pdf.cli.check_screen_recording_permission', return_value=True)
    mocker.patch('capture_pdf.cli.check_accessibility_permission', return_value=True)

    runner = CliRunner()
    output = tmp_path / "book.pdf"
    result = runner.invoke(cli, ['screenshot', '--pages', '3', '--output', str(output)])

    assert result.exit_code == 0, f"CLI failed: {result.output}"


def test_cli_shows_progress(tmp_path, mocker):
    """CLI should show capture progress."""
    from capture_pdf.cli import cli
    from PIL import Image

    mock_image = Image.new('RGB', (800, 1000), color='white')
    mock_capturer = mocker.patch('capture_pdf.cli.ScreenCapturer')
    mock_capturer.return_value.capture_region.return_value = mock_image
    mock_capturer.return_value.capture_full_screen.return_value = mock_image

    mocker.patch('capture_pdf.cli.PageNavigator')
    mocker.patch('capture_pdf.cli.check_screen_recording_permission', return_value=True)
    mocker.patch('capture_pdf.cli.check_accessibility_permission', return_value=True)

    runner = CliRunner()
    output = tmp_path / "book.pdf"
    result = runner.invoke(cli, ['screenshot', '--pages', '3', '--output', str(output)])

    assert "1/3" in result.output or "Page 1" in result.output or "Capturing" in result.output


def test_cli_warns_on_missing_permissions(mocker):
    """CLI should warn when permissions are missing."""
    from capture_pdf.cli import cli

    mocker.patch('capture_pdf.cli.check_screen_recording_permission', return_value=False)
    mocker.patch('capture_pdf.cli.check_accessibility_permission', return_value=True)

    runner = CliRunner()
    result = runner.invoke(cli, ['screenshot', '--pages', '3', '--output', 'test.pdf'])

    assert result.exit_code != 0
    assert "permission" in result.output.lower() or "screen recording" in result.output.lower()
