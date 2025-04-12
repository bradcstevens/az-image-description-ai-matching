"""
Main image analyzer module to coordinate analysis and matching of food images.
"""
import os
import re
import json
import shutil
import glob
from typing import Dict, Any, List, Optional, Tuple
from tqdm import tqdm

from app.config.settings import settings
from app.utils.file_utils import (
    sanitize_filename
)


class ImageAnalyzer:
    """
    Main class that coordinates image analysis and matching using Azure services.
    """
    
    def __init__(
        self, 
        openai_service=None, 
        vision_service=None, 
        descriptions=None
    ):
        """
        Initialize the image analyzer with required components.
        
        Args:
            openai_service: Instance of AzureOpenAIService for image analysis.
            vision_service: Instance of AzureVisionService for image analysis.
            descriptions: List of food descriptions to match against.
        """
        self.openai_service = openai_service
        self.vision_service = vision_service
        self.descriptions = descriptions or []
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze a single image using available AI services.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            Combined analysis results with best match.
        """
        # Validate the image path
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        vision_analysis = None
        openai_analysis = None
        combined_analysis = None
        
        # If both services are available, use them together
        if self.vision_service and self.openai_service:
            try:
                # Analyze with Azure AI Vision first to provide context for OpenAI
                vision_analysis = self.vision_service.analyze_image(image_path)
                
                # Analyze with Azure OpenAI, passing Vision results
                openai_analysis = self.openai_service.analyze_image(
                    image_path, 
                    self.descriptions, 
                    vision_analysis
                )
                
                # Combine the results from both services
                combined_analysis = self.combine_analysis_results(openai_analysis, vision_analysis)
            except Exception as e:
                print(f"Error during combined analysis: {str(e)}")
                raise
        
        # If only OpenAI is available
        elif self.openai_service:
            try:
                # Analyze with OpenAI only
                openai_analysis = self.openai_service.analyze_image(
                    image_path, 
                    self.descriptions, 
                    None
                )
                combined_analysis = openai_analysis
            except Exception as e:
                print(f"Error during OpenAI analysis: {str(e)}")
                raise
        
        # If only Vision is available
        elif self.vision_service:
            try:
                # Analyze with Vision only
                vision_analysis = self.vision_service.analyze_image(image_path)
                
                # Create a description from vision results
                vision_description = f"Caption: {vision_analysis['caption']}\n"
                if vision_analysis['text']:
                    vision_description += "TEXT DETECTED: " + " | ".join(
                        [item["text"] for item in vision_analysis["text"]]
                    ) + "\n"
                if vision_analysis['tags']:
                    vision_description += "Tags: " + ", ".join(
                        [tag["name"] for tag in vision_analysis["tags"][:10]]
                    ) + "\n"
                
                combined_analysis = {
                    "description": vision_description,
                    "file_name": os.path.basename(image_path),
                    "vision_analysis": vision_analysis
                }
            except Exception as e:
                print(f"Error during Vision analysis: {str(e)}")
                raise
        
        else:
            # No services available
            raise ValueError("No AI services available for image analysis")
        
        if not combined_analysis:
            raise ValueError("Analysis failed to produce a result")
        
        # Find the best match for the image
        match_result = self.find_best_match(combined_analysis)
        
        # Add match information to the result
        combined_analysis.update(match_result)
        
        # Create a match filename
        match_filename = self._create_match_filename(combined_analysis)
        combined_analysis["match_filename"] = match_filename
        
        return combined_analysis
    
    def combine_analysis_results(
        self, 
        openai_analysis: Dict[str, Any], 
        vision_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combine results from OpenAI and Azure Vision services.
        
        Args:
            openai_analysis: Results from OpenAI analysis.
            vision_analysis: Results from Azure Vision analysis.
            
        Returns:
            Combined analysis results.
        """
        combined_description = openai_analysis["description"]
        confidence_boost = 0
        synergy_notes = []
        
        # If we have Azure Vision results, enhance the OpenAI description
        if vision_analysis:
            # Extract any text detected by Vision API to help with identification
            detected_text = ""
            if vision_analysis["text"]:
                text_items = [item["text"] for item in vision_analysis["text"] if item["confidence"] > 0.5]
                if text_items:
                    detected_text = " | ".join(text_items)
            
            # Add Vision API detected text if not already in the OpenAI response
            if detected_text and "TEXT DETECTED:" not in combined_description:
                combined_description = f"TEXT DETECTED: {detected_text}\n" + combined_description
                synergy_notes.append("Added Vision API text detection")
            
            # Add tags from Vision API if helpful
            if vision_analysis["tags"]:
                # Only include high-confidence food-related tags
                food_tags = [tag["name"] for tag in vision_analysis["tags"] 
                           if tag["confidence"] > 0.7 and tag["name"] in 
                           ["food", "sandwich", "bread", "burger", "meal", "lunch", "dinner", "breakfast", 
                            "plate", "meat", "cheese", "vegetable", "dessert", "salad", "wrap"]]
                if food_tags:
                    # Add Vision API food tags if not already in the description
                    added_tags = []
                    for tag in food_tags:
                        if tag.lower() not in combined_description.lower():
                            combined_description += f"\nVision API detected: {tag}"
                            added_tags.append(tag)
                    
                    if added_tags:
                        synergy_notes.append(f"Added Vision API food tags: {', '.join(added_tags)}")
            
            # Print a comparison of the two models' results
            self._print_model_comparison(openai_analysis, vision_analysis, synergy_notes, confidence_boost)
        
        return {
            "description": combined_description,
            "file_name": openai_analysis["file_name"],
            "confidence_boost": confidence_boost,
            "synergy_notes": synergy_notes,
            "analysis_methods": ["openai", "azure_vision"],
            "openai_analysis": openai_analysis,
            "vision_analysis": vision_analysis
        }
    
    def find_best_match(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find the best matching food description based on analysis results.
        
        Args:
            analysis: Image analysis results.
            
        Returns:
            Match results with confidence score.
        """
        text = analysis["description"].lower()
        
        # Extract detected text from the image (if any)
        detected_text = ""
        text_match = re.search(r'text detected:\s*(.*?)(?:\n|$)', text, re.IGNORECASE)
        if text_match:
            detected_text = text_match.group(1).strip().lower()
            print(f"Text detected in image: {detected_text}")
        
        # Try to extract confidence score from the description
        confidence_score = 0
        confidence_match = re.search(r'confidence[\s:]*(score)?[\s:]*([\d\.]+)(?:\/10)?', text, re.IGNORECASE)
        if confidence_match:
            try:
                confidence_score = float(confidence_match.group(2))
                if confidence_score > 10:  # Normalize to 1-10 scale if needed
                    confidence_score = confidence_score / 10
            except ValueError:
                confidence_score = 0
        
        # Check if OpenAI explicitly returned an UNMATCHED result
        unmatched_pattern = r'unmatched[\s\-]*([\w\s]+)'
        unmatched_match = re.search(unmatched_pattern, text, re.IGNORECASE)
        
        # Start regular matching process
        best_match = None
        best_score = 0
        
        # Look for exact match with detected text first if available
        if detected_text:
            for description in self.descriptions:
                desc_normalized = description.lower()
                
                # If we have an exact match between detected text and description
                if detected_text in desc_normalized or desc_normalized in detected_text:
                    best_match = description
                    best_score = 0.9  # High confidence for text match
                    break
        
        # If no match found with detected text, try content matching
        if best_match is None:
            for description in self.descriptions:
                # Normalize the description for better matching
                desc_normalized = description.lower()
                
                # Split description into words
                desc_words = desc_normalized.split()
                
                # Calculate score based on word presence
                base_score = 0
                for word in desc_words:
                    if len(word) > 2 and word in text:  # Only count words with length > 2
                        base_score += 1
                
                # Calculate final score
                if len(desc_words) > 0:
                    normalized_score = base_score / len(desc_words)
                    
                    if normalized_score > best_score:
                        best_score = normalized_score
                        best_match = description
        
        # Apply confidence boost from synergy if available
        confidence_boost = analysis.get("confidence_boost", 0)
        
        # If OpenAI explicitly marked this as UNMATCHED, create unmatched result with AI-provided confidence
        if unmatched_match:
            unmatched_desc = unmatched_match.group(1).strip().upper()
            
            # Use the AI-provided confidence if available, otherwise use calculated best_score
            if confidence_score > 0:
                base_confidence = confidence_score / 10  # Scale to 0-1 range
            else:
                # Use a more meaningful confidence based on best_score for unmatched items
                base_confidence = max(0.3, best_score) 
            
            final_confidence = base_confidence + confidence_boost
            final_confidence = min(final_confidence, 0.9)  # Cap at 0.9 since it's unmatched
            
            result = {
                "match": f"UNMATCHED {unmatched_desc}",
                "score": best_score,
                "confidence": final_confidence,
                "original_confidence": base_confidence,
                "synergy_boost": confidence_boost,
                "is_explicit_unmatched": True,
                "unmatched_reason": "AI explicitly marked as unmatched"
            }
        else:
            # If we have a confidence score from the model, factor it in
            if confidence_score > 0:
                final_confidence = (confidence_score / 10) + confidence_boost
                # Cap confidence at 1.0
                final_confidence = min(final_confidence, 1.0)
            else:
                final_confidence = best_score + confidence_boost
                # Cap confidence at 1.0
                final_confidence = min(final_confidence, 1.0)
            
            result = {
                "match": best_match if best_match else None,
                "score": best_score,
                "confidence": final_confidence,
                "original_confidence": confidence_score / 10 if confidence_score > 0 else best_score,
                "synergy_boost": confidence_boost
            }
        
            # If no good match found or score is too low, create a formatted unmatched description
            if best_match is None or best_score < 0.3:
                # Create a generic unmatched description
                food_words = []
                food_description = re.sub(r'text detected:.*?\n', '', text, flags=re.IGNORECASE)  # Remove detected text
                food_description = re.sub(r'confidence score:.*?\n', '', food_description, flags=re.IGNORECASE)
                
                # Extract key food words based on the description
                for word in food_description.split():
                    if len(word) > 2 and word.isalpha():
                        food_words.append(word.upper())
                
                # Create abbreviated description in the same style as other menu items
                abbrev_desc = ' '.join(food_words[:4])  # Limit to 4 words
                result["match"] = f"UNMATCHED {abbrev_desc}"
                result["unmatched_reason"] = "No good match found"
        
        # Add synergy notes if available
        if "synergy_notes" in analysis:
            result["synergy_notes"] = analysis.get("synergy_notes", [])
        
        # Add analysis methods if available
        if "analysis_methods" in analysis:
            result["analysis_methods"] = analysis.get("analysis_methods", [])
        
        return result
    
    def _create_match_filename(self, analysis: Dict[str, Any]) -> str:
        """
        Create a filename based on the match result.
        
        Args:
            analysis: Analysis results with match information.
            
        Returns:
            Generated filename for the matched image.
        """
        # Get the original filename 
        orig_filename = analysis.get("file_name", "unknown.jpeg")
        _, ext = os.path.splitext(orig_filename)
        
        # If we have a match, use it as the base for the new filename
        if analysis.get("match"):
            match_description = analysis["match"]
            confidence = analysis.get("confidence", 0)
            
            # For unmatched items, create a more informative filename
            if match_description.startswith("UNMATCHED"):
                # Extract the food description after "UNMATCHED"
                food_description = match_description[9:].strip()
                
                # Clean up food description for filename
                food_description = re.sub(r'CONFIDENCE[^\w]*SCORE.*', '', food_description, flags=re.IGNORECASE).strip()
                food_description = re.sub(r'\s+', '_', food_description)  # Replace spaces with underscores
                
                # Handle any unusual characters
                food_description = sanitize_filename(food_description)
                
                # Format confidence as a percentage with clearer meaning
                conf_pct = int(confidence * 100)
                
                # Create the new filename with UNMATCHED prefix and confidence
                return f"UNMATCHED_{food_description}_conf{conf_pct}{ext}"
            else:
                # This is a matched item - clean up the description for filename
                clean_description = sanitize_filename(match_description)
                clean_description = re.sub(r'\s+', '_', clean_description)  # Replace spaces with underscores
                
                # Format confidence as a percentage
                conf_pct = int(confidence * 100)
                
                # Create the new filename
                return f"{clean_description}_conf{conf_pct}{ext}"
        else:
            # If no match, return the original filename
            return orig_filename
            
    def _print_model_comparison(
        self, 
        openai_analysis: Dict[str, Any], 
        vision_analysis: Dict[str, Any],
        synergy_notes: List[str],
        confidence_boost: float
    ) -> None:
        """
        Print a comparison of the OpenAI and Azure Vision model results.
        
        Args:
            openai_analysis: OpenAI analysis results.
            vision_analysis: Azure Vision analysis results.
            synergy_notes: List of synergy enhancement notes.
            confidence_boost: Confidence boost value.
        """
        print("\n===== COMPARING OPENAI AND AZURE VISION RESULTS =====")
        
        # Compare captions
        openai_caption_match = re.search(r'(?:^|\n)([^:]*?)(?:Confidence|$)', openai_analysis["description"])
        openai_caption = openai_caption_match.group(1).strip() if openai_caption_match else ""
        vision_caption = vision_analysis["caption"]
        
        print(f"OpenAI caption: {openai_caption}")
        print(f"Azure Vision caption: {vision_caption}")
        
        # Compare text detection
        openai_text_match = re.search(r'TEXT DETECTED:\s*(.*?)(?:\n|$)', openai_analysis["description"], re.IGNORECASE)
        openai_text = openai_text_match.group(1).strip() if openai_text_match else "None"
        vision_text = ", ".join([item["text"] for item in vision_analysis["text"]]) if vision_analysis["text"] else "None"
        
        print(f"\nOpenAI detected text: {openai_text}")
        print(f"Azure Vision detected text: {vision_text}")
        
        # Print synergy notes
        if synergy_notes:
            print("\nSynergy enhancements:")
            for note in synergy_notes:
                print(f"- {note}")
            print(f"Total confidence boost: {confidence_boost:.2f}")
        
        print("===============================================\n")