"""Tests for permissions module."""


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
