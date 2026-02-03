"""Page navigation using macOS Quartz keyboard and mouse simulation."""
import time
from enum import IntEnum
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventPost,
    CGEventSetFlags,
    CGEventCreateMouseEvent,
    CGEventSetIntegerValueField,
    kCGHIDEventTap,
    kCGEventFlagMaskShift,
    kCGEventFlagMaskCommand,
    kCGEventMouseMoved,
    kCGEventLeftMouseDown,
    kCGEventLeftMouseUp,
    kCGMouseButtonLeft,
    kCGMouseEventClickState,
)
from Quartz.CoreGraphics import CGPointMake


class KeyCode(IntEnum):
    """macOS virtual key codes."""
    RIGHT_ARROW = 0x7C
    LEFT_ARROW = 0x7B
    UP_ARROW = 0x7E
    DOWN_ARROW = 0x7D
    RETURN = 0x24
    TAB = 0x30
    SPACE = 0x31
    DELETE = 0x33
    ESCAPE = 0x35
    F1 = 0x7A
    F2 = 0x78
    F3 = 0x63
    F4 = 0x76
    F5 = 0x60
    KEY_A = 0x00
    KEY_S = 0x01
    KEY_D = 0x02
    KEY_F = 0x03
    KEY_N = 0x2D
    KEY_P = 0x23
    KEY_0 = 0x1D
    KEY_1 = 0x12
    KEY_2 = 0x13
    KEY_3 = 0x14
    PAGE_UP = 0x74
    PAGE_DOWN = 0x79
    HOME = 0x73
    END = 0x77


class PageNavigator:
    """Page navigation using macOS Quartz keyboard simulation."""

    def __init__(self, page_delay: float = 1.0):
        self.page_delay = page_delay

    def press_key(self, key_code: KeyCode, modifiers: int = 0) -> None:
        """Simulate a key press (down + up)."""
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
        time.sleep(0.05)

        event_up = CGEventCreateKeyboardEvent(None, key_code, False)
        if modifiers:
            CGEventSetFlags(event_up, modifiers)

        CGEventPost(kCGHIDEventTap, event_up)
        time.sleep(0.05)

    def press_key_with_command(self, key_code: KeyCode) -> None:
        """Press a key with Command modifier."""
        self.press_key(key_code, modifiers=kCGEventFlagMaskCommand)

    def click(self, x: int, y: int) -> None:
        """
        Simulate a mouse click at the specified coordinates.

        Args:
            x: X coordinate in pixels
            y: Y coordinate in pixels
        """
        point = CGPointMake(x, y)

        # Move mouse to position
        move_event = CGEventCreateMouseEvent(None, kCGEventMouseMoved, point, kCGMouseButtonLeft)
        CGEventPost(kCGHIDEventTap, move_event)
        time.sleep(0.05)

        # Mouse down
        down_event = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, point, kCGMouseButtonLeft)
        CGEventSetIntegerValueField(down_event, kCGMouseEventClickState, 1)
        CGEventPost(kCGHIDEventTap, down_event)
        time.sleep(0.05)

        # Mouse up
        up_event = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, point, kCGMouseButtonLeft)
        CGEventSetIntegerValueField(up_event, kCGMouseEventClickState, 1)
        CGEventPost(kCGHIDEventTap, up_event)
        time.sleep(0.1)

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

    def click_and_wait(self, x: int, y: int, wait: float = 0.5) -> None:
        """Click at coordinates and wait."""
        self.click(x, y)
        time.sleep(wait)
