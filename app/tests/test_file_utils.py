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
    create_timestamped_directory,
    is_git_lfs_pointer,
    validate_image_file
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
        
        # Create a git-lfs pointer file
        self.lfs_pointer_file = os.path.join(self.test_dir, "lfs_pointer.jpg")
        with open(self.lfs_pointer_file, "w") as f:
            f.write("version https://git-lfs.github.com/spec/v1\n")
            f.write("oid sha256:04dd80b4cd94d766a0ff32ad2539ff8830255d80983b2798c4801611d6961c33\n")
            f.write("size 584060\n")
        
        # Create an empty file
        self.empty_file = os.path.join(self.test_dir, "empty.jpg")
        with open(self.empty_file, "w") as f:
            pass
    
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
    
    def test_is_git_lfs_pointer(self):
        """Test git lfs pointer detection."""
        # Test with an actual Git LFS pointer file
        self.assertTrue(is_git_lfs_pointer(self.lfs_pointer_file))
        
        # Test with a regular image file
        self.assertFalse(is_git_lfs_pointer(self.test_image))
        
        # Test with empty file
        self.assertFalse(is_git_lfs_pointer(self.empty_file))
        
        # Test with nonexistent file (should not raise exception)
        self.assertFalse(is_git_lfs_pointer(os.path.join(self.test_dir, "nonexistent.jpg")))
    
    def test_validate_image_file(self):
        """Test image file validation."""
        # Test with valid image
        is_valid, error_msg = validate_image_file(self.test_image)
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")
        
        # Test with LFS pointer
        is_valid, error_msg = validate_image_file(self.lfs_pointer_file)
        self.assertFalse(is_valid)
        self.assertTrue("Git LFS pointer" in error_msg)
        
        # Test with empty file
        is_valid, error_msg = validate_image_file(self.empty_file)
        self.assertFalse(is_valid)
        self.assertTrue("empty" in error_msg)
        
        # Test with nonexistent file
        nonexistent_file = os.path.join(self.test_dir, "nonexistent.jpg")
        is_valid, error_msg = validate_image_file(nonexistent_file)
        self.assertFalse(is_valid)
        self.assertTrue("does not exist" in error_msg)


if __name__ == "__main__":
    unittest.main() 