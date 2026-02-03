"""Tests for page navigation module."""
import time
from unittest.mock import patch


def test_simulate_key_press_does_not_raise():
    """Simulating a key press should complete without error."""
    from capture_pdf.navigator import PageNavigator, KeyCode
    navigator = PageNavigator()
    # Should not raise exception
    navigator.press_key(KeyCode.RIGHT_ARROW)


def test_next_page_sends_right_arrow():
    """Next page should send right arrow key."""
    from capture_pdf.navigator import PageNavigator, KeyCode
    navigator = PageNavigator()
    with patch.object(navigator, 'press_key') as mock_press:
        navigator.next_page()
        mock_press.assert_called_once_with(KeyCode.RIGHT_ARROW)


def test_previous_page_sends_left_arrow():
    """Previous page should send left arrow key."""
    from capture_pdf.navigator import PageNavigator, KeyCode
    navigator = PageNavigator()
    with patch.object(navigator, 'press_key') as mock_press:
        navigator.previous_page()
        mock_press.assert_called_once_with(KeyCode.LEFT_ARROW)


def test_wait_for_page_respects_delay():
    """Wait should pause for specified duration."""
    from capture_pdf.navigator import PageNavigator
    navigator = PageNavigator(page_delay=0.5)
    start = time.time()
    navigator.wait_for_page()
    elapsed = time.time() - start
    assert elapsed >= 0.5


def test_click_does_not_raise():
    """Clicking should complete without error."""
    from capture_pdf.navigator import PageNavigator
    navigator = PageNavigator()
    # Should not raise exception (clicks at 100, 100)
    navigator.click(100, 100)
