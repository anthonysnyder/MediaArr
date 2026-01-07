"""
Unified artwork service for managing backdrops, logos, and posters
"""

import os
import re
import urllib.parse
import requests
import time
from datetime import datetime
from difflib import SequenceMatcher
from typing import List, Optional, Tuple

from utils import safe_listdir, ImageProcessor
from utils.mapping_utils import get_mapped_directory, save_mapped_directory
from utils.file_utils import safe_file_write, safe_file_remove


class ArtworkService:
    """Handles all artwork-related operations"""

    # File extensions for each artwork type
    ARTWORK_EXTENSIONS = {
        'backdrop': ['jpg', 'jpeg', 'png'],
        'logo': ['png', 'jpg', 'jpeg'],
        'poster': ['jpg', 'jpeg', 'png']
    }

    # Simple cache for scan results (cache for 60 seconds)
    _scan_cache = {}
    _cache_duration = 60  # seconds

    @staticmethod
    def normalize_title(title: str) -> str:
        """
        Normalize movie/TV show titles for consistent searching and comparison.

        Args:
            title: Title to normalize

        Returns:
            Normalized title (lowercase, alphanumeric only)
        """
        return re.sub(r'[^a-z0-9]+', '', title.lower())

    @staticmethod
    def strip_leading_the(title: str) -> str:
        """
        Remove leading "The " from titles for more accurate sorting.

        Args:
            title: Title to process

        Returns:
            Title without leading "The "
        """
        if title.lower().startswith("the "):
            return title[4:]
        return title

    @staticmethod
    def generate_clean_id(title: str) -> str:
        """
        Generate a URL-friendly and anchor-safe ID from the media title.

        Args:
            title: Media title

        Returns:
            Clean ID for use in HTML anchors and URLs
        """
        clean_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        return clean_id

    @staticmethod
    def get_artwork_info(directory_path: str, artwork_type: str) -> dict:
        """
        Get information about a specific artwork type in a directory.

        Args:
            directory_path: Path to media directory
            artwork_type: 'backdrop', 'logo', or 'poster'

        Returns:
            Dictionary with artwork info (path, thumb_path, dimensions, etc.)
        """
        info = {
            'path': None,
            'thumb_path': None,
            'web_path': None,
            'web_thumb_path': None,
            'dimensions': None,
            'last_modified': None,
            'has_artwork': False
        }

        directory_name = os.path.basename(directory_path)
        extensions = ArtworkService.ARTWORK_EXTENSIONS[artwork_type]

        for ext in extensions:
            artwork_file = f"{artwork_type}.{ext}"
            thumb_file = f"{artwork_type}-thumb.{ext}"

            artwork_path = os.path.join(directory_path, artwork_file)
            thumb_path = os.path.join(directory_path, thumb_file)

            if os.path.exists(thumb_path):
                info['thumb_path'] = thumb_path
                info['web_thumb_path'] = f"/artwork/{urllib.parse.quote(directory_name)}/{thumb_file}"

            if os.path.exists(artwork_path):
                info['path'] = artwork_path
                info['web_path'] = f"/artwork/{urllib.parse.quote(directory_name)}/{artwork_file}"
                info['has_artwork'] = True

                # Get dimensions
                info['dimensions'] = ImageProcessor.get_image_dimensions(artwork_path)

                # Get last modified date
                timestamp = os.path.getmtime(artwork_path)
                info['last_modified'] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

                break

        return info

    @staticmethod
    def scan_media_directories(base_folders: List[str]) -> Tuple[List[dict], int]:
        """
        Scan media directories and collect all artwork information.
        Optimized to reduce file system operations on SMB mounts.
        Uses simple time-based caching to avoid re-scanning on every page load.

        Args:
            base_folders: List of base folder paths to scan

        Returns:
            Tuple of (list of media items, total count)
        """
        # Create cache key from folder paths
        cache_key = ','.join(sorted(base_folders))

        # Check cache
        if cache_key in ArtworkService._scan_cache:
            cached_data, cached_time = ArtworkService._scan_cache[cache_key]
            if time.time() - cached_time < ArtworkService._cache_duration:
                return cached_data, len(cached_data)

        media_list = []

        for base_folder in base_folders:
            for media_dir in sorted(safe_listdir(base_folder)):
                # Skip Synology NAS system folders and hidden files
                if media_dir.lower() in ["@eadir", "#recycle"] or media_dir.startswith('.'):
                    continue

                media_path = os.path.join(base_folder, media_dir)

                # Optimization: Skip os.path.isdir() check - assume everything is a directory
                # This saves a file system operation per directory on SMB mounts
                # If it's not a directory, safe_listdir will return empty list
                try:
                    dir_files = set(safe_listdir(media_path))
                    # If listdir returned nothing and it's actually a file, skip it
                    if not dir_files and '.' in media_dir:
                        continue
                except:
                    # If we can't list the directory, skip it
                    continue

                # Build media item with inline artwork checking (reduces function call overhead)
                clean_id = ArtworkService.generate_clean_id(media_dir)
                directory_name = os.path.basename(media_path)

                media_item = {
                    'title': media_dir,
                    'directory_path': media_path,
                    'clean_id': clean_id,
                }

                # Check each artwork type efficiently
                for artwork_type in ['backdrop', 'logo', 'poster']:
                    has_artwork = False
                    web_path = None
                    web_thumb_path = None
                    dimensions = None
                    last_modified = None

                    # Check for artwork files (in order of preference)
                    for ext in ArtworkService.ARTWORK_EXTENSIONS[artwork_type]:
                        artwork_file = f'{artwork_type}.{ext}'
                        thumb_file = f'{artwork_type}-thumb.{ext}'

                        # Use cached dir listing instead of os.path.exists()
                        if artwork_file in dir_files:
                            has_artwork = True
                            web_path = f"/artwork/{urllib.parse.quote(directory_name)}/{artwork_file}"

                            # Only check thumb if we found the main artwork
                            if thumb_file in dir_files:
                                web_thumb_path = f"/artwork/{urllib.parse.quote(directory_name)}/{thumb_file}"

                            # Skip expensive operations (dimensions, mtime) - not needed for listing
                            # These will be fetched on-demand if needed
                            break

                    # Add to media item
                    media_item[f'{artwork_type}'] = web_path
                    media_item[f'{artwork_type}_thumb'] = web_thumb_path
                    media_item[f'{artwork_type}_dimensions'] = dimensions
                    media_item[f'{artwork_type}_last_modified'] = last_modified
                    media_item[f'has_{artwork_type}'] = has_artwork

                media_list.append(media_item)

        # Sort by title, ignoring leading "The"
        media_list = sorted(
            media_list,
            key=lambda x: ArtworkService.strip_leading_the(x['title'].lower())
        )

        # Store in cache
        ArtworkService._scan_cache[cache_key] = (media_list, time.time())

        return media_list, len(media_list)

    @staticmethod
    def download_and_save_artwork(
        artwork_url: str,
        artwork_type: str,
        media_title: str,
        save_dir: str
    ) -> Optional[str]:
        """
        Download artwork and generate thumbnail.

        Args:
            artwork_url: URL to download artwork from
            artwork_type: 'backdrop', 'logo', or 'poster'
            media_title: Title of media (for logging)
            save_dir: Directory to save artwork to

        Returns:
            Path to saved artwork file, or None on failure
        """
        # Determine file extension and paths based on artwork type
        if artwork_type == 'logo':
            # Logos should be PNG to preserve transparency
            ext = 'png'
        else:
            # Backdrops and posters are typically JPG
            ext = 'jpg'

        full_path = os.path.join(save_dir, f'{artwork_type}.{ext}')
        thumb_path = os.path.join(save_dir, f'{artwork_type}-thumb.{ext}')

        try:
            # Remove any existing artwork files using SMB-safe removal
            for e in ArtworkService.ARTWORK_EXTENSIONS[artwork_type]:
                existing_file = os.path.join(save_dir, f'{artwork_type}.{e}')
                existing_thumb = os.path.join(save_dir, f'{artwork_type}-thumb.{e}')

                safe_file_remove(existing_file)
                safe_file_remove(existing_thumb)

            # Download the artwork
            response = requests.get(artwork_url)
            if response.status_code != 200:
                print(f"Failed to download {artwork_type} for '{media_title}'. Status: {response.status_code}")
                return None

            # Save the full-resolution artwork using SMB-safe write
            safe_file_write(full_path, response.content)

            # Create thumbnail based on artwork type
            success = False
            if artwork_type == 'backdrop':
                success = ImageProcessor.create_backdrop_thumbnail(full_path, thumb_path)
            elif artwork_type == 'logo':
                success = ImageProcessor.create_logo_thumbnail(full_path, thumb_path)
            elif artwork_type == 'poster':
                success = ImageProcessor.create_poster_thumbnail(full_path, thumb_path)

            if success:
                print(f"{artwork_type.capitalize()} and thumbnail saved successfully for '{media_title}'")
                return full_path
            else:
                print(f"Failed to create thumbnail for '{media_title}'")
                return full_path  # Still return path even if thumbnail failed

        except Exception as e:
            print(f"Error saving {artwork_type} for '{media_title}': {e}")
            return None

    @staticmethod
    def find_matching_directory(
        media_title: str,
        tmdb_id: int,
        media_type: str,
        base_folders: List[str],
        directory_hint: str = None
    ) -> Optional[str]:
        """
        Find the matching directory for a media item using three-tier strategy.

        Tier 1: Use directory hint if provided (from UI click)
        Tier 2: Check TMDb mapping file
        Tier 3: Fuzzy match with normalized titles

        Args:
            media_title: Title of the media
            tmdb_id: TMDb ID
            media_type: 'movie' or 'tv'
            base_folders: List of base folders to search
            directory_hint: Directory name passed from UI (optional)

        Returns:
            Full path to matching directory, or None if not found
        """
        # TIER 1: Use directory hint from UI click
        if directory_hint:
            for base_folder in base_folders:
                potential_path = os.path.join(base_folder, directory_hint)
                if os.path.exists(potential_path) and os.path.isdir(potential_path):
                    print(f"Using directory from UI hint: {potential_path}")
                    # Save this mapping for future use
                    save_mapped_directory(tmdb_id, media_type, potential_path)
                    return potential_path

        # TIER 2: Check TMDb mapping file
        mapped_dir = get_mapped_directory(tmdb_id, media_type)
        if mapped_dir:
            print(f"Using previously saved directory mapping: {mapped_dir}")
            return mapped_dir

        # TIER 3: Fuzzy matching
        normalized_title = ArtworkService.normalize_title(media_title)
        best_similarity = 0
        best_match_dir = None

        for base_folder in base_folders:
            directories = safe_listdir(base_folder)

            for directory in directories:
                # Skip system folders
                if directory.lower() in ["@eadir", "#recycle"]:
                    continue

                normalized_dir = ArtworkService.normalize_title(directory)
                similarity = SequenceMatcher(None, normalized_title, normalized_dir).ratio()

                print(f"Comparing '{media_title}' with '{directory}': similarity {similarity:.3f}")

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_dir = os.path.join(base_folder, directory)

                # Check for exact match
                if normalized_title == normalized_dir:
                    print(f"Exact match found: {directory}")
                    save_mapped_directory(tmdb_id, media_type, os.path.join(base_folder, directory))
                    return os.path.join(base_folder, directory)

        # Use best match if similarity is high enough (0.9 threshold)
        if best_similarity >= 0.9:
            print(f"Using fuzzy match: {best_match_dir} (similarity: {best_similarity:.3f})")
            save_mapped_directory(tmdb_id, media_type, best_match_dir)
            return best_match_dir

        print(f"No suitable match found for '{media_title}' (best similarity: {best_similarity:.3f})")
        return None
