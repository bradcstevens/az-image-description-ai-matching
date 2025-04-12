"""
Unit tests for the AzureVisionService class.
"""
import unittest
from unittest.mock import patch, MagicMock

from app.core.azure_vision import AzureVisionService


class TestAzureVisionService(unittest.TestCase):
    """Test case for AzureVisionService."""
    
    def test_init(self):
        """Test initialization of AzureVisionService."""
        # Test with default values
        service = AzureVisionService()
        self.assertIsNotNone(service.analyzer)
        
        # Test with custom values
        service = AzureVisionService(
            endpoint="https://custom-endpoint.com",
            key="custom-api-key"
        )
        self.assertEqual(service.analyzer.endpoint, "https://custom-endpoint.com")
        self.assertEqual(service.analyzer.key, "custom-api-key")
    
    @patch('app.core.azure_vision.VisionAnalyzer.test_connection')
    def test_is_available(self, mock_test_connection):
        """Test is_available method."""
        # Test when connection is successful
        mock_test_connection.return_value = True
        service = AzureVisionService()
        self.assertTrue(service.is_available())
        
        # Test when connection fails
        mock_test_connection.return_value = False
        self.assertFalse(service.is_available())
    
    @patch('app.core.azure_vision.VisionAnalyzer.analyze_image')
    def test_analyze_image(self, mock_analyze_image):
        """Test analyze_image method."""
        # Setup mock
        expected_result = {
            "caption": "test caption",
            "caption_confidence": 0.9,
            "tags": [{"name": "food", "confidence": 0.8}],
            "objects": [],
            "text": []
        }
        mock_analyze_image.return_value = expected_result
        
        # Test the method
        service = AzureVisionService()
        result = service.analyze_image(image_path="test.jpg")
        
        # Check result
        self.assertEqual(result, expected_result)
        
        # Verify analyze_image was called with correct parameters
        mock_analyze_image.assert_called_once_with(image_path="test.jpg")
    
    @patch('app.core.azure_vision.VisionAnalyzer.analyze_image')
    def test_analyze_image_error(self, mock_analyze_image):
        """Test analyze_image method with an error."""
        # Setup mock to simulate an error
        mock_analyze_image.side_effect = Exception("Test error")
        
        # Test the method - should not raise an exception
        service = AzureVisionService()
        result = service.analyze_image(image_path="test.jpg")
        
        # Check that the result contains empty values due to error handling in VisionAnalyzer
        self.assertEqual(result["caption"], "")
        self.assertEqual(result["caption_confidence"], 0.0)
        self.assertEqual(result["tags"], [])
        self.assertEqual(result["objects"], [])
        self.assertEqual(result["text"], [])
        
        # Verify analyze_image was called with correct parameters
        mock_analyze_image.assert_called_once_with(image_path="test.jpg")


if __name__ == "__main__":
    unittest.main() 