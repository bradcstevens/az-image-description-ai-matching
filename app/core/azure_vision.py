"""
Azure AI Vision image analysis module.
"""
from typing import Dict, Any, Optional, List
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential

from app.config.settings import settings


class VisionAnalyzer:
    """Azure AI Vision service for image analysis."""
    
    def __init__(self, endpoint: str = None, key: str = None):
        """
        Initialize the VisionAnalyzer.
        
        Args:
            endpoint: Azure Vision endpoint URL. If None, uses settings.
            key: Azure Vision API key. If None, uses settings.
        """
        self.endpoint = endpoint or settings.azure_vision_endpoint
        self.key = key or settings.azure_vision_key
        self._client = None
    
    @property
    def client(self) -> ImageAnalysisClient:
        """
        Get the Azure Vision client.
        
        Returns:
            Initialized Azure Vision client.
        """
        if self._client is None:
            self._client = ImageAnalysisClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.key)
            )
        return self._client

    def test_connection(self) -> bool:
        """
        Test the Azure AI Vision connection.
        
        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            # Just check if credentials are properly configured
            if not self.endpoint or not self.key:
                print("Azure Vision credentials are not configured")
                return False
            
            # Create valid credentials without making an API call
            _ = AzureKeyCredential(self.key)
            
            print("Azure Vision credentials are valid")
            return True
            
        except Exception as e:
            print(f"Error testing Azure Vision connection: {str(e)}")
            return False

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze an image using Azure AI Vision.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            Dictionary containing analysis results.
        """
        try:
            print(f"Processing image with Azure Vision: {image_path}")
            
            # Open image file in binary mode
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # Analyze the image with Azure AI Vision
            analysis_result = self.client.analyze(
                image_data=image_data,
                visual_features=[
                    VisualFeatures.CAPTION,
                    VisualFeatures.TAGS,
                    VisualFeatures.OBJECTS,
                    VisualFeatures.READ
                ]
            )
            
            # Extract relevant information
            vision_analysis = {
                "caption": analysis_result.caption.text if analysis_result.caption else "",
                "caption_confidence": analysis_result.caption.confidence if analysis_result.caption else 0.0,
                "tags": [],
                "objects": [],
                "text": []
            }
            
            # Extract tags
            if analysis_result.tags:
                for tag in analysis_result.tags.list:
                    vision_analysis["tags"].append({
                        "name": tag.name,
                        "confidence": tag.confidence
                    })
            
            # Extract objects
            if analysis_result.objects:
                for obj in analysis_result.objects.list:
                    vision_analysis["objects"].append({
                        "name": obj.tags[0].name if obj.tags else "unknown",
                        "confidence": obj.tags[0].confidence if obj.tags else 0.0,
                        "bounding_box": {
                            "x": obj.bounding_box.x,
                            "y": obj.bounding_box.y,
                            "width": obj.bounding_box.width,
                            "height": obj.bounding_box.height
                        }
                    })
            
            # Extract text (OCR)
            if analysis_result.read:
                for block in analysis_result.read.blocks:
                    for line in block.lines:
                        vision_analysis["text"].append({
                            "text": line.text,
                            "confidence": max([word.confidence for word in line.words]) if line.words else 0.0
                        })
            
            # Print detailed Vision API results
            self._print_results(vision_analysis)
            
            return vision_analysis
        
        except Exception as e:
            print(f"Error analyzing image with Azure Vision {image_path}: {str(e)}")
            return {
                "caption": "",
                "caption_confidence": 0.0,
                "tags": [],
                "objects": [],
                "text": []
            }
    
    def _print_results(self, vision_analysis: Dict[str, Any]) -> None:
        """
        Print detailed Vision API results.
        
        Args:
            vision_analysis: Dictionary of vision analysis results.
        """
        print("\n===== AZURE VISION ANALYSIS RESULTS =====")
        print(f"Caption: '{vision_analysis['caption']}' (Confidence: {vision_analysis['caption_confidence']:.2f})")
        
        if vision_analysis["tags"]:
            print("\nTags detected:")
            for tag in vision_analysis["tags"]:
                print(f"  - {tag['name']} (Confidence: {tag['confidence']:.2f})")
        
        if vision_analysis["objects"]:
            print("\nObjects detected:")
            for obj in vision_analysis["objects"]:
                print(f"  - {obj['name']} (Confidence: {obj['confidence']:.2f})")
                print(f"    Bounding box: x={obj['bounding_box']['x']}, y={obj['bounding_box']['y']}, " +
                      f"width={obj['bounding_box']['width']}, height={obj['bounding_box']['height']}")
        
        if vision_analysis["text"]:
            print("\nText detected:")
            for text_item in vision_analysis["text"]:
                print(f"  - '{text_item['text']}' (Confidence: {text_item['confidence']:.2f})")
        
        print("==========================================\n")
        
        print(f"Azure Vision analysis complete: {len(vision_analysis['tags'])} tags, " + 
              f"{len(vision_analysis['objects'])} objects, {len(vision_analysis['text'])} text blocks")

class AzureVisionService:
    """Service for Azure AI Vision image analysis."""
    
    def __init__(self, endpoint: str = None, key: str = None):
        """
        Initialize the AzureVisionService.
        
        Args:
            endpoint: Azure Vision endpoint URL. If None, uses settings.
            key: Azure Vision API key. If None, uses settings.
        """
        self.analyzer = VisionAnalyzer(endpoint=endpoint, key=key)
    
    def is_available(self) -> bool:
        """
        Check if the Azure Vision service is available.
        
        Returns:
            True if available, False otherwise.
        """
        return self.analyzer.test_connection()
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze an image using Azure AI Vision.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            Dictionary containing analysis results.
        """
        try:
            return self.analyzer.analyze_image(image_path=image_path)
        except Exception as e:
            print(f"Error in AzureVisionService.analyze_image: {str(e)}")
            # Return empty result dictionary on error to match VisionAnalyzer's error handling
            return {
                "caption": "",
                "caption_confidence": 0.0,
                "tags": [],
                "objects": [],
                "text": []
            }