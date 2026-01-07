"""
Image processing utilities for creating thumbnails
"""

from PIL import Image
import os


class ImageProcessor:
    """Handles image processing for different artwork types"""

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

                # Save as JPEG with high quality
                img_resized.save(output_path, "JPEG", quality=90)

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

                # Save as PNG to preserve transparency
                img_resized.save(output_path, "PNG", optimize=True)

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

                # Save the thumbnail image with high JPEG quality
                img_resized.save(output_path, "JPEG", quality=90)

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
