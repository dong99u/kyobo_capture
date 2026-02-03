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
