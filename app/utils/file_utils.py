"""
File utility functions for the Azure Image Description AI Matching application.
"""
import os
import re
import base64
import datetime
from typing import List, Dict, Any, Optional, Tuple


def is_git_lfs_pointer(file_path: str) -> bool:
    """
    Check if a file is a Git LFS pointer rather than actual content.
    
    Args:
        file_path: Path to the file to check.
        
    Returns:
        True if the file is a Git LFS pointer, False otherwise.
    """
    try:
        # Check file size - Git LFS pointers are very small (typically <200 bytes)
        if os.path.getsize(file_path) > 1000:
            return False
            
        # Read the first line of the file to check for Git LFS signature
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            first_line = f.readline().strip()
            return first_line.startswith('version https://git-lfs.github.com/spec/')
    except Exception:
        return False


def load_descriptions_from_file(file_path: str) -> List[str]:
    """
    Load menu item descriptions from a text file.

    Args:
        file_path: Path to the text file containing descriptions.

    Returns:
        List of descriptions, one per line.
    """
    try:
        with open(file_path, 'r') as f:
            descriptions = [line.strip() for line in f.readlines() if line.strip()]
        return descriptions
    except FileNotFoundError:
        print(f"Error: Descriptions file not found at {file_path}")
        return []
    except Exception as e:
        print(f"Error reading descriptions file: {str(e)}")
        return []


def sanitize_filename(name: str) -> str:
    """
    Convert a description to a valid filename by removing invalid characters.

    Args:
        name: Input filename to sanitize.

    Returns:
        Sanitized filename with invalid characters replaced by underscores.
    """
    # Replace any character that's not alphanumeric, dash, or underscore with underscore
    # Use the ASCII flag to ensure only ASCII alphanumeric characters are preserved
    return re.sub(r'[^\w\-]', '_', name, flags=re.ASCII)


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image to base64 format.

    Args:
        image_path: Path to the image file.

    Returns:
        Base64 encoded string of the image.
    """
    # First check if this is a Git LFS pointer
    if is_git_lfs_pointer(image_path):
        raise ValueError("This file is a Git LFS pointer, not an actual image. Run 'git lfs pull' to download the actual images.")
    
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error encoding image {image_path}: {str(e)}")
        return ""


def ensure_directory_exists(directory: str) -> None:
    """
    Create directory if it doesn't exist.

    Args:
        directory: Path to the directory to create.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def create_timestamped_directory(base_dir: str) -> str:
    """
    Create a timestamped directory under the base directory.

    Args:
        base_dir: Base directory path.

    Returns:
        Path to the created timestamped directory.
    """
    # Ensure base directory exists
    ensure_directory_exists(base_dir)
    
    # Create a timestamp string in format YYYY-MM-DD_HH-MM-SS
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Create the timestamped directory
    timestamped_dir = os.path.join(base_dir, timestamp)
    ensure_directory_exists(timestamped_dir)
    
    return timestamped_dir


def validate_image_file(image_path: str) -> Tuple[bool, str]:
    """
    Validate that a file is a proper image and not a Git LFS pointer.
    
    Args:
        image_path: Path to the image file to validate.
        
    Returns:
        A tuple of (is_valid, error_message) where is_valid is a boolean
        indicating if the file is a valid image, and error_message is 
        a string containing an error message if not valid, or an empty string.
    """
    # Check if file exists
    if not os.path.exists(image_path):
        return False, f"File does not exist: {image_path}"
    
    # Check if file is empty
    if os.path.getsize(image_path) == 0:
        return False, f"File is empty: {image_path}"
    
    # Check if file is a Git LFS pointer
    if is_git_lfs_pointer(image_path):
        return False, (f"File is a Git LFS pointer, not an actual image. "
                      f"Run 'git lfs pull' to download the actual images.")
    
    # Additional validation could be added here (e.g., checking magic bytes for image formats)
    
    return True, ""