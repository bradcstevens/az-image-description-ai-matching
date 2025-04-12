"""
Unit tests for the AzureOpenAIService class.
"""
import unittest
from unittest.mock import patch, MagicMock

from app.core.azure_openai import AzureOpenAIService


class TestAzureOpenAIService(unittest.TestCase):
    """Test case for AzureOpenAIService."""
    
    def test_init(self):
        """Test initialization of AzureOpenAIService."""
        # Test with default values
        service = AzureOpenAIService()
        self.assertIsNotNone(service.analyzer)
        
        # Test with custom values
        service = AzureOpenAIService(
            endpoint="https://custom-endpoint.com",
            api_key="custom-api-key",
            api_version="2023-06-01-preview",
            deployment="custom-deployment"
        )
        self.assertEqual(service.analyzer.endpoint, "https://custom-endpoint.com")
        self.assertEqual(service.analyzer.api_key, "custom-api-key")
        self.assertEqual(service.analyzer.api_version, "2023-06-01-preview")
        self.assertEqual(service.analyzer.deployment, "custom-deployment")
    
    @patch('app.core.azure_openai.OpenAIAnalyzer.test_connection')
    def test_is_available(self, mock_test_connection):
        """Test is_available method."""
        # Test when connection is successful
        mock_test_connection.return_value = True
        service = AzureOpenAIService()
        self.assertTrue(service.is_available())
        
        # Test when connection fails
        mock_test_connection.return_value = False
        self.assertFalse(service.is_available())
    
    @patch('app.core.azure_openai.OpenAIAnalyzer.analyze_image')
    def test_analyze_image(self, mock_analyze_image):
        """Test analyze_image method."""
        # Setup mock
        expected_result = {"description": "Test description", "file_name": "test.jpg"}
        mock_analyze_image.return_value = expected_result
        
        # Test the method
        service = AzureOpenAIService()
        result = service.analyze_image(
            image_path="test.jpg",
            descriptions=["Test description"],
            vision_results={"caption": "test"}
        )
        
        # Check result
        self.assertEqual(result, expected_result)
        
        # Verify analyze_image was called with correct parameters
        mock_analyze_image.assert_called_once_with(
            image_path="test.jpg", 
            descriptions=["Test description"], 
            vision_results={"caption": "test"}
        )
    
    @patch('app.core.azure_openai.OpenAIAnalyzer.analyze_image')
    def test_analyze_image_without_vision(self, mock_analyze_image):
        """Test analyze_image method without vision results."""
        # Setup mock
        expected_result = {"description": "Test description", "file_name": "test.jpg"}
        mock_analyze_image.return_value = expected_result
        
        # Test the method
        service = AzureOpenAIService()
        result = service.analyze_image(
            image_path="test.jpg",
            descriptions=["Test description"],
        )
        
        # Check result
        self.assertEqual(result, expected_result)
        
        # Verify analyze_image was called with correct parameters
        mock_analyze_image.assert_called_once_with(
            image_path="test.jpg", 
            descriptions=["Test description"], 
            vision_results=None
        )


if __name__ == "__main__":
    unittest.main() 