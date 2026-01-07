"""
File utilities for SMB-safe operations
"""

import os
import time
from flask import send_file


def safe_listdir(path: str, retries: int = 8, base_delay: float = 0.05):
    """
    Safely list directory contents with retry logic for SMB mounts.
    Degrades gracefully on BlockingIOError instead of raising 500 errors.

    Args:
        path: Directory path to list
        retries: Number of retry attempts
        base_delay: Initial delay in seconds (exponential backoff)

    Returns:
        List of directory contents, or empty list on failure
    """
    last_exc = None
    for attempt in range(retries):
        try:
            return os.listdir(path)
        except BlockingIOError as e:
            last_exc = e
            time.sleep(base_delay * (2 ** attempt))
    return []  # Degrade gracefully, never 500


def safe_send_file(path: str, retries: int = 8, base_delay: float = 0.05, **kwargs):
    """
    Safely send a file with retry logic for SMB mounts.
    Handles BlockingIOError by retrying with exponential backoff.

    Args:
        path: File path to send
        retries: Number of retry attempts
        base_delay: Initial delay in seconds (exponential backoff)
        **kwargs: Additional arguments to pass to send_file

    Returns:
        Flask response object

    Raises:
        BlockingIOError: If all retries fail
    """
    last_exc = None
    for attempt in range(retries):
        try:
            return send_file(path, **kwargs)
        except BlockingIOError as e:
            last_exc = e
            if attempt < retries - 1:  # Don't sleep on the last attempt
                time.sleep(base_delay * (2 ** attempt))

    # If all retries fail, raise the last exception
    raise last_exc
