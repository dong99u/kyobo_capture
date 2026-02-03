"""Screen capture using macOS Quartz APIs."""
from dataclasses import dataclass
from pathlib import Path

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
    """Capture region in PIXEL coordinates (not points)."""
    x: int
    y: int
    width: int
    height: int


def cg_image_to_pil(cg_image) -> Image.Image:
    """Convert a Quartz CGImage to a PIL Image."""
    width = CGImageGetWidth(cg_image)
    height = CGImageGetHeight(cg_image)
    bytes_per_row = CGImageGetBytesPerRow(cg_image)

    data_provider = CGImageGetDataProvider(cg_image)
    cf_data = CGDataProviderCopyData(data_provider)
    data_length = CFDataGetLength(cf_data)

    buffer = bytearray(data_length)
    CFDataGetBytes(cf_data, (0, data_length), buffer)

    arr = np.frombuffer(buffer, dtype=np.uint8)
    arr = arr.reshape((height, bytes_per_row // 4, 4))
    arr = arr[:, :width, :]
    arr = arr[:, :, [2, 1, 0, 3]]

    return Image.fromarray(arr, mode='RGBA')


class ScreenCapturer:
    """Screen capture using macOS Quartz APIs."""

    def __init__(self, scale_factor: float = 1.0):
        self.scale_factor = scale_factor

    def capture_full_screen(self) -> Image.Image:
        """Capture the entire screen."""
        cg_image = CGWindowListCreateImage(
            CGRectInfinite,
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID,
            0
        )
        if cg_image is None:
            raise RuntimeError(
                "Screen capture failed. Please ensure Screen Recording permission is granted "
                "in System Preferences > Privacy & Security > Screen Recording"
            )
        return cg_image_to_pil(cg_image)

    def capture_region(self, region: CaptureRegion) -> Image.Image:
        """Capture a specific region of the screen."""
        rect = CGRectMake(region.x, region.y, region.width, region.height)
        cg_image = CGWindowListCreateImage(
            rect,
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID,
            0
        )
        if cg_image is None:
            raise RuntimeError("Region capture failed. Check Screen Recording permission.")
        image = cg_image_to_pil(cg_image)

        # If captured image is larger than requested (due to Retina scaling),
        # resize it to the requested dimensions
        if image.width != region.width or image.height != region.height:
            image = image.resize((region.width, region.height), Image.Resampling.LANCZOS)

        return image

    def save(self, image: Image.Image, path: Path) -> None:
        """Save image to file."""
        image.save(path)
