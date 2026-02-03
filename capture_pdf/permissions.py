"""macOS permission checking utilities."""
from Quartz import CGPreflightScreenCaptureAccess, CGRequestScreenCaptureAccess


def check_screen_recording_permission() -> bool:
    """Check if screen recording permission is granted."""
    return CGPreflightScreenCaptureAccess()


def request_screen_recording_permission() -> bool:
    """Request screen recording permission from user."""
    return CGRequestScreenCaptureAccess()


def check_accessibility_permission() -> bool:
    """Check if accessibility permission is granted."""
    from ApplicationServices import AXIsProcessTrusted
    return AXIsProcessTrusted()
