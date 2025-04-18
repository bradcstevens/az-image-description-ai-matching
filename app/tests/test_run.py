"""
Unit tests for the run.py module.
"""
import os
import unittest
from unittest.mock import patch
import subprocess

# Import the function to test
import sys
import os.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from run import run_git_lfs_pull


class TestRunModule(unittest.TestCase):
    """Test case for functions in the run.py module."""
    
    @patch('subprocess.run')
    def test_git_lfs_pull_success(self, mock_run):
        """Test successful git lfs pull operation."""
        # Mock successful subprocess run calls
        mock_run.return_value.stdout = b'Git LFS initialized.\ndownloaded 10 files'
        mock_run.return_value.stderr = b''
        
        success, message = run_git_lfs_pull()
        
        self.assertTrue(success)
        self.assertIn("Successfully pulled LFS files", message)
        
        # Verify subprocess was called correctly
        self.assertEqual(mock_run.call_count, 2)
        # First call should check git lfs version
        self.assertEqual(mock_run.call_args_list[0][0][0][:3], ['git', 'lfs', '--version'])
        # Second call should run git lfs pull
        self.assertEqual(mock_run.call_args_list[1][0][0], ['git', 'lfs', 'pull'])
    
    @patch('subprocess.run')
    def test_git_lfs_pull_not_installed(self, mock_run):
        """Test git lfs pull when git lfs is not installed."""
        # Mock FileNotFoundError for subprocess
        mock_run.side_effect = FileNotFoundError("No such file or directory: 'git'")
        
        success, message = run_git_lfs_pull()
        
        self.assertFalse(success)
        self.assertIn("not installed", message)
    
    @patch('subprocess.run')
    def test_git_lfs_pull_command_error(self, mock_run):
        """Test git lfs pull when command fails."""
        class MockCompletedProcess:
            def __init__(self, stdout=b'', stderr=b''):
                self.stdout = stdout
                self.stderr = stderr
        
        # First call succeeds (git lfs --version), second fails (git lfs pull)
        def side_effect(*args, **kwargs):
            if args[0][1] == 'lfs' and args[0][2] == '--version':
                return MockCompletedProcess(stdout=b'git-lfs/3.0.2')
            else:
                raise subprocess.CalledProcessError(
                    returncode=1, 
                    cmd='git lfs pull', 
                    stderr=b'error: failed to pull some objects'
                )
        
        mock_run.side_effect = side_effect
        
        success, message = run_git_lfs_pull()
        
        self.assertFalse(success)
        self.assertIn("Git LFS command failed", message)


if __name__ == "__main__":
    unittest.main() 