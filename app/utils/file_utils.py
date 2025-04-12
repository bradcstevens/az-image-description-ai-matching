"""
File utility functions for the Azure Image Description AI Matching application.
"""
import os
import re
import base64
import datetime
from typing import List, Dict, Any, Optional


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