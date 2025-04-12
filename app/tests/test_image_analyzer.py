"""
Unit tests for the ImageAnalyzer class.
"""
import os
import unittest
from unittest.mock import patch, MagicMock, call

from app.core.image_analyzer import ImageAnalyzer


class TestImageAnalyzer(unittest.TestCase):
    """Test case for ImageAnalyzer."""
    
    def test_init(self):
        """Test initialization of ImageAnalyzer."""
        # Test with default values
        analyzer = ImageAnalyzer()
        self.assertIsNone(analyzer.openai_service)
        self.assertIsNone(analyzer.vision_service)
        self.assertEqual(len(analyzer.descriptions), 0)
        
        # Test with custom values
        openai_service = MagicMock()
        vision_service = MagicMock()
        descriptions = ["description1", "description2"]
        
        analyzer = ImageAnalyzer(
            openai_service=openai_service,
            vision_service=vision_service,
            descriptions=descriptions
        )
        self.assertEqual(analyzer.openai_service, openai_service)
        self.assertEqual(analyzer.vision_service, vision_service)
        self.assertEqual(analyzer.descriptions, descriptions)
    
    def test_analyze_image(self):
        """Test analyze_image method using both services together."""
        # Setup mocks
        openai_service = MagicMock()
        openai_service.analyze_image.return_value = {
            "description": "test openai description",
            "file_name": "test.jpg"
        }
        
        vision_service = MagicMock()
        vision_service.analyze_image.return_value = {
            "caption": "test vision caption",
            "caption_confidence": 0.9,
            "tags": [{"name": "food", "confidence": 0.8}],
            "objects": [],
            "text": [{"text": "food text", "confidence": 0.7}]
        }
        
        # Create analyzer with both services
        analyzer = ImageAnalyzer(
            openai_service=openai_service,
            vision_service=vision_service,
            descriptions=["description1", "description2"]
        )
        
        # Mock combine_analysis_results and find_best_match to return simple results
        analyzer.combine_analysis_results = MagicMock(return_value={
            "description": "combined description",
            "file_name": "test.jpg",
            "confidence_boost": 0.1,
            "synergy_notes": ["note1", "note2"],
            "analysis_methods": ["openai", "azure_vision"],
            "openai_analysis": openai_service.analyze_image.return_value,
            "vision_analysis": vision_service.analyze_image.return_value
        })
        
        analyzer.find_best_match = MagicMock(return_value={
            "match": "description1",
            "score": 0.9,
            "confidence": 0.9
        })
        
        # Call the method
        result = analyzer.analyze_image("test.jpg")
        
        # Verify services were called
        vision_service.analyze_image.assert_called_once_with("test.jpg")
        openai_service.analyze_image.assert_called_once_with(
            "test.jpg", 
            ["description1", "description2"], 
            vision_service.analyze_image.return_value
        )
        
        # Verify combine_analysis_results was called
        analyzer.combine_analysis_results.assert_called_once_with(
            openai_service.analyze_image.return_value,
            vision_service.analyze_image.return_value
        )
        
        # Verify find_best_match was called
        analyzer.find_best_match.assert_called_once()
        
        # Check result contains expected keys
        self.assertIn("description", result)
        self.assertIn("file_name", result)
        self.assertIn("match", result)
        self.assertIn("score", result)
        self.assertIn("confidence", result)
        self.assertIn("match_filename", result)
    
    def test_find_best_match_with_explicit_unmatched(self):
        """Test find_best_match method with explicit unmatched result."""
        # Setup analyzer
        analyzer = ImageAnalyzer(descriptions=["description1", "description2"])
        
        # Setup input with unmatched result
        analysis = {
            "description": "UNMATCHED CHICKEN SNDWCH\nConfidence score: 8/10",
            "file_name": "test.jpg"
        }
        
        # Call the method
        result = analyzer.find_best_match(analysis)
        
        # Check result
        self.assertIn("match", result)
        self.assertTrue(result["match"].startswith("UNMATCHED"))
        self.assertIn("is_explicit_unmatched", result)
        self.assertTrue(result["is_explicit_unmatched"])
    
    def test_find_best_match_with_good_match(self):
        """Test find_best_match method with a good match."""
        # Setup analyzer
        analyzer = ImageAnalyzer(descriptions=[
            "Chicken Sandwich", 
            "Turkey Club", 
            "Veggie Wrap"
        ])
        
        # Setup input with text that should match
        analysis = {
            "description": "This is a chicken sandwich with lettuce.\nConfidence score: 9/10",
            "file_name": "test.jpg"
        }
        
        # Call the method
        result = analyzer.find_best_match(analysis)
        
        # Check result
        self.assertIn("match", result)
        self.assertEqual(result["match"], "Chicken Sandwich")
        self.assertGreater(result["confidence"], 0.5)
    
    def test_find_best_match_with_detected_text(self):
        """Test find_best_match method with detected text."""
        # Setup analyzer
        analyzer = ImageAnalyzer(descriptions=[
            "Chicken Sandwich", 
            "Turkey Club", 
            "Veggie Wrap"
        ])
        
        # Setup input with detected text that matches a description
        analysis = {
            "description": "TEXT DETECTED: Turkey Club\nThis looks like a sandwich.\nConfidence score: 7/10",
            "file_name": "test.jpg"
        }
        
        # Call the method
        result = analyzer.find_best_match(analysis)
        
        # Check result
        self.assertIn("match", result)
        self.assertEqual(result["match"], "Turkey Club")
        self.assertGreater(result["score"], 0.8)  # High score due to text match
    
    def test_create_match_filename(self):
        """Test _create_match_filename method."""
        # Setup analyzer
        analyzer = ImageAnalyzer()
        
        # Test with match
        analysis = {
            "match": "Chicken Sandwich",
            "confidence": 0.85,
            "file_name": "test.jpg"
        }
        
        filename = analyzer._create_match_filename(analysis)
        self.assertTrue(filename.startswith("Chicken_Sandwich"))
        self.assertTrue(filename.endswith(".jpg"))
        
        # Test with unmatched
        analysis = {
            "match": "UNMATCHED CHICKEN SNDWCH",
            "confidence": 0.25,
            "file_name": "test.jpg"
        }
        
        filename = analyzer._create_match_filename(analysis)
        self.assertTrue(filename.startswith("UNMATCHED_CHICKEN_SNDWCH"))
        self.assertTrue(filename.endswith(".jpg"))
        
        # Test without match
        analysis = {
            "file_name": "test.jpg"
        }
        
        filename = analyzer._create_match_filename(analysis)
        self.assertEqual(filename, "test.jpg")


if __name__ == "__main__":
    unittest.main() 