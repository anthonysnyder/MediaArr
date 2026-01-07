"""
Image processing utilities for creating thumbnails
"""

from PIL import Image
import os
import time
import io


class ImageProcessor:
    """Handles image processing for different artwork types"""

    @staticmethod
    def _safe_image_save(img, output_path: str, format: str, retries: int = 8, base_delay: float = 0.05, **save_kwargs):
        """
        Safely save PIL Image with retry logic for SMB mounts.
        First saves to memory buffer, then writes to file with retry logic.

        Args:
            img: PIL Image object
            output_path: Path to save image
            format: Image format (e.g., "JPEG", "PNG")
            retries: Number of retry attempts
            base_delay: Initial delay in seconds (exponential backoff)
            **save_kwargs: Additional arguments for img.save()

        Returns:
            True on success

        Raises:
            BlockingIOError or OSError: If all retries fail
        """
        # First, save to memory buffer
        buffer = io.BytesIO()
        img.save(buffer, format, **save_kwargs)
        content = buffer.getvalue()

        # Then write to file with retry logic
        last_exc = None
        for attempt in range(retries):
            try:
                with open(output_path, 'wb') as f:
                    f.write(content)
                return True
            except (BlockingIOError, OSError) as e:
                last_exc = e
                if attempt < retries - 1:
                    time.sleep(base_delay * (2 ** attempt))

        # If all retries fail, raise the last exception
        raise last_exc

    @staticmethod
    def create_backdrop_thumbnail(source_path: str, output_path: str):
        """
        Create backdrop thumbnail with 16:9 aspect ratio (300x169).
        Uses center cropping to maintain aspect ratio.

        Args:
            source_path: Path to source image
            output_path: Path to save thumbnail
        """
        try:
            with Image.open(source_path) as img:
                # Target 16:9 aspect ratio
                target_ratio = 16 / 9
                aspect_ratio = img.width / img.height

                # Crop to 16:9 if needed
                if aspect_ratio > target_ratio:
                    # Image is wider than 16:9, crop sides
                    new_width = int(img.height * target_ratio)
                    left = (img.width - new_width) // 2
                    img = img.crop((left, 0, left + new_width, img.height))
                elif aspect_ratio < target_ratio:
                    # Image is taller than 16:9, crop top/bottom
                    new_height = int(img.width / target_ratio)
                    top = (img.height - new_height) // 2
                    img = img.crop((0, top, img.width, top + new_height))

                # Resize to 300x169
                img_resized = img.resize((300, 169), Image.LANCZOS)

                # Save as JPEG with high quality using SMB-safe save
                ImageProcessor._safe_image_save(img_resized, output_path, "JPEG", quality=90)

            return True

        except Exception as e:
            print(f"Error creating backdrop thumbnail: {e}")
            return False

    @staticmethod
    def create_logo_thumbnail(source_path: str, output_path: str):
        """
        Create logo thumbnail with max width of 500px.
        Maintains aspect ratio and preserves transparency (PNG).

        Args:
            source_path: Path to source image
            output_path: Path to save thumbnail
        """
        try:
            with Image.open(source_path) as img:
                max_width = 500
                aspect_ratio = img.width / img.height

                # Calculate thumbnail dimensions maintaining aspect ratio
                if img.width > max_width:
                    new_width = max_width
                    new_height = int(max_width / aspect_ratio)
                else:
                    new_width = img.width
                    new_height = img.height

                # Resize with high-quality Lanczos resampling
                img_resized = img.resize((new_width, new_height), Image.LANCZOS)

                # Save as PNG to preserve transparency using SMB-safe save
                ImageProcessor._safe_image_save(img_resized, output_path, "PNG", optimize=True)

            return True

        except Exception as e:
            print(f"Error creating logo thumbnail: {e}")
            return False

    @staticmethod
    def create_poster_thumbnail(source_path: str, output_path: str):
        """
        Create poster thumbnail with 2:3 aspect ratio (300x450).
        Uses center cropping to maintain aspect ratio.

        Args:
            source_path: Path to source image
            output_path: Path to save thumbnail
        """
        try:
            with Image.open(source_path) as img:
                # Target 2:3 aspect ratio (poster)
                target_ratio = 300 / 450  # 2:3
                aspect_ratio = img.width / img.height

                # Crop to 2:3 if needed
                if aspect_ratio > target_ratio:
                    # Image is wider than desired ratio, crop the sides
                    new_width = int(img.height * target_ratio)
                    left = (img.width - new_width) // 2
                    img = img.crop((left, 0, left + new_width, img.height))
                else:
                    # Image is taller than desired ratio, crop the top and bottom
                    new_height = int(img.width / target_ratio)
                    top = (img.height - new_height) // 2
                    img = img.crop((0, top, img.width, top + new_height))

                # Resize the image to 300x450 pixels with high-quality Lanczos resampling
                img_resized = img.resize((300, 450), Image.LANCZOS)

                # Save the thumbnail image with high JPEG quality using SMB-safe save
                ImageProcessor._safe_image_save(img_resized, output_path, "JPEG", quality=90)

            return True

        except Exception as e:
            print(f"Error creating poster thumbnail: {e}")
            return False

    @staticmethod
    def get_image_dimensions(image_path: str) -> str:
        """
        Get image dimensions as a formatted string.

        Args:
            image_path: Path to image file

        Returns:
            Dimensions as "WIDTHxHEIGHT" or "Unknown" on error
        """
        try:
            with Image.open(image_path) as img:
                return f"{img.width}x{img.height}"
        except Exception:
            return "Unknown"
