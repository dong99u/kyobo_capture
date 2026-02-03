"""PDF compilation from images."""
from pathlib import Path
from typing import List

from PIL import Image


class PDFCompiler:
    """Compile multiple images into a single PDF."""

    def compile(self, images: List[Image.Image], output_path: Path, dpi: float = 150.0) -> None:
        """
        Compile a list of PIL Images into a single PDF.

        Args:
            images: List of PIL Image objects
            output_path: Path for output PDF file
            dpi: Resolution in dots per inch (default: 150, use 300 for print quality)
        """
        if not images:
            raise ValueError("No images provided")

        # Convert to RGB if necessary (PDF doesn't support RGBA)
        rgb_images = []
        for img in images:
            if img.mode == 'RGBA':
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                rgb_images.append(background)
            elif img.mode != 'RGB':
                rgb_images.append(img.convert('RGB'))
            else:
                rgb_images.append(img)

        # Save first image with append_images for subsequent pages
        first_image = rgb_images[0]
        if len(rgb_images) > 1:
            first_image.save(
                output_path,
                "PDF",
                save_all=True,
                append_images=rgb_images[1:],
                resolution=dpi
            )
        else:
            first_image.save(output_path, "PDF", resolution=dpi)

    def compile_from_files(self, image_paths: List[Path], output_path: Path, dpi: float = 150.0) -> None:
        """
        Compile images from file paths into a single PDF.

        Args:
            image_paths: List of paths to image files
            output_path: Path for output PDF file
            dpi: Resolution in dots per inch (default: 150, use 300 for print quality)
        """
        images = [Image.open(path) for path in image_paths]
        self.compile(images, output_path, dpi=dpi)
        # Close opened images
        for img in images:
            img.close()
