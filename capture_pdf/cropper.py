"""Margin detection and page cropping for PDFs."""
import tempfile
from dataclasses import dataclass
from pathlib import Path

import img2pdf
import numpy as np
from PIL import Image
from pdf2image import convert_from_path


@dataclass(frozen=True)
class CropBox:
    """Bounding box for the content area after margin removal."""
    left: int
    top: int
    right: int
    bottom: int


class MarginDetector:
    """Detect margin boundaries on PIL Images using numpy array analysis."""

    def __init__(self, mode: str = 'auto', threshold: int = 10):
        self.mode = mode
        self.threshold = threshold

    def detect(self, image: Image.Image) -> CropBox:
        """Detect margin boundaries and return the content bounding box."""
        arr = np.array(image.convert('RGB'))
        h, w, _ = arr.shape

        margin_color = self._resolve_margin_color(arr)

        top = self._scan_from_top(arr, margin_color)
        bottom = self._scan_from_bottom(arr, margin_color)
        left = self._scan_from_left(arr, margin_color)
        right = self._scan_from_right(arr, margin_color)

        return CropBox(left=left, top=top, right=right, bottom=bottom)

    def _resolve_margin_color(self, arr: np.ndarray) -> np.ndarray:
        if self.mode == 'black':
            return np.array([0, 0, 0])
        elif self.mode == 'white':
            return np.array([255, 255, 255])
        else:
            return self._auto_detect_margin_color(arr)

    def _auto_detect_margin_color(self, arr: np.ndarray) -> np.ndarray:
        """Sample 4 corner pixels and classify margin color."""
        h, w, _ = arr.shape
        corners = [
            arr[0, 0],
            arr[0, w - 1],
            arr[h - 1, 0],
            arr[h - 1, w - 1],
        ]
        median = np.median(corners, axis=0)

        if np.all(median <= self.threshold):
            return np.array([0, 0, 0])
        elif np.all(median >= 255 - self.threshold):
            return np.array([255, 255, 255])
        else:
            return np.array([255, 255, 255])  # fallback to white

    def _is_margin_row(self, row: np.ndarray, color: np.ndarray) -> bool:
        return bool(np.all(np.abs(row.astype(int) - color.astype(int)) <= self.threshold))

    def _is_margin_col(self, col: np.ndarray, color: np.ndarray) -> bool:
        return bool(np.all(np.abs(col.astype(int) - color.astype(int)) <= self.threshold))

    def _scan_from_top(self, arr: np.ndarray, color: np.ndarray) -> int:
        for i in range(arr.shape[0]):
            if not self._is_margin_row(arr[i], color):
                return i
        return 0

    def _scan_from_bottom(self, arr: np.ndarray, color: np.ndarray) -> int:
        for i in range(arr.shape[0] - 1, -1, -1):
            if not self._is_margin_row(arr[i], color):
                return i + 1
        return arr.shape[0]

    def _scan_from_left(self, arr: np.ndarray, color: np.ndarray) -> int:
        for i in range(arr.shape[1]):
            if not self._is_margin_col(arr[:, i], color):
                return i
        return 0

    def _scan_from_right(self, arr: np.ndarray, color: np.ndarray) -> int:
        for i in range(arr.shape[1] - 1, -1, -1):
            if not self._is_margin_col(arr[:, i], color):
                return i + 1
        return arr.shape[1]


class PageCropper:
    """Crop PDF pages by detecting and removing margins."""

    def __init__(self, detector: MarginDetector, padding: int = 0):
        self.detector = detector
        self.padding = padding

    def crop_pdf(self, input_path: Path, output_path: Path, dpi: int = 300) -> None:
        """Crop all pages in a PDF and write to output."""
        pages = convert_from_path(str(input_path), dpi=dpi)

        if not pages:
            raise ValueError("PDF has no pages")

        with tempfile.TemporaryDirectory() as tmpdir:
            cropped_paths = []
            for i, page in enumerate(pages):
                box = self.detector.detect(page)
                cropped = page.crop((box.left, box.top, box.right, box.bottom))

                if self.padding > 0:
                    padded = Image.new(
                        'RGB',
                        (cropped.width + 2 * self.padding, cropped.height + 2 * self.padding),
                        color=(255, 255, 255),
                    )
                    padded.paste(cropped, (self.padding, self.padding))
                    cropped = padded

                tmp_path = Path(tmpdir) / f"page_{i}.png"
                cropped.save(tmp_path, dpi=(dpi, dpi))
                cropped_paths.append(str(tmp_path))

            with open(output_path, "wb") as f:
                f.write(img2pdf.convert(cropped_paths))
