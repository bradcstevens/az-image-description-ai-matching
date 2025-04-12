"""
Unit tests for the file_utils module.
"""
import os
import shutil
import tempfile
import unittest
from datetime import datetime

from app.utils.file_utils import (
    load_descriptions_from_file,
    sanitize_filename,
    encode_image_to_base64,
    ensure_directory_exists,
    create_timestamped_directory
)


class TestFileUtils(unittest.TestCase):
    """Test case for file utility functions."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Create a temporary descriptions file
        self.descriptions_file = os.path.join(self.test_dir, "test_descriptions.txt")
        with open(self.descriptions_file, "w") as f:
            f.write("Test description 1\n")
            f.write("Test description 2\n")
            f.write("Test description 3\n")
        
        # Create a small test image
        self.test_image = os.path.join(self.test_dir, "test_image.jpg")
        with open(self.test_image, "wb") as f:
            # Create a minimal JPEG file
            f.write(bytes.fromhex("FFD8FFE000104A46494600010101006000600000FFDB004300FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC0000B08000100010101011100FFC40014100100000000000000000000000000000000FFDA0008010100013F10"))
    
    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.test_dir)
    
    def test_load_descriptions_from_file(self):
        """Test loading descriptions from a file."""
        # Test with existing file
        descriptions = load_descriptions_from_file(self.descriptions_file)
        self.assertEqual(len(descriptions), 3)
        self.assertEqual(descriptions[0], "Test description 1")
        self.assertEqual(descriptions[1], "Test description 2")
        self.assertEqual(descriptions[2], "Test description 3")
        
        # Test with nonexistent file
        descriptions = load_descriptions_from_file(os.path.join(self.test_dir, "nonexistent.txt"))
        self.assertEqual(len(descriptions), 0)
    
    def test_sanitize_filename(self):
        """Test sanitizing filenames."""
        # Test with spaces and special characters
        self.assertEqual(sanitize_filename("Hello World!"), "Hello_World_")
        
        # Test with path separators
        self.assertEqual(sanitize_filename("path/to/file"), "path_to_file")
        
        # Test with non-ASCII characters
        self.assertEqual(sanitize_filename("ñáéíóú"), "______")
        
        # Edge case: empty string
        self.assertEqual(sanitize_filename(""), "")
    
    def test_encode_image_to_base64(self):
        """Test encoding image to base64."""
        # Test with valid image file
        encoded = encode_image_to_base64(self.test_image)
        self.assertTrue(len(encoded) > 0)
        
        # Test with invalid path
        encoded = encode_image_to_base64(os.path.join(self.test_dir, "nonexistent.jpg"))
        self.assertEqual(encoded, "")
    
    def test_ensure_directory_exists(self):
        """Test creating directory if it doesn't exist."""
        # Test with new directory
        new_dir = os.path.join(self.test_dir, "new_directory")
        ensure_directory_exists(new_dir)
        self.assertTrue(os.path.exists(new_dir))
        
        # Test with existing directory (should not raise exception)
        ensure_directory_exists(new_dir)
        self.assertTrue(os.path.exists(new_dir))
    
    def test_create_timestamped_directory(self):
        """Test creating a timestamped directory."""
        # Get current date
        now = datetime.now()
        year_month_day = now.strftime("%Y-%m-%d")
        
        # Create timestamped directory
        timestamped_dir = create_timestamped_directory(self.test_dir)
        
        # Check that directory exists
        self.assertTrue(os.path.exists(timestamped_dir))
        
        # Check that directory name contains current date
        dir_name = os.path.basename(timestamped_dir)
        self.assertTrue(dir_name.startswith(year_month_day))


if __name__ == "__main__":
    unittest.main() 