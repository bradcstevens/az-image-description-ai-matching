"""
Azure OpenAI image analysis module.
"""
import os
from typing import Dict, Any, Optional, List
from openai import AzureOpenAI

from app.config.settings import settings
from app.utils.file_utils import encode_image_to_base64


class OpenAIAnalyzer:
    """Azure OpenAI service for image analysis."""
    
    def __init__(
        self, 
        endpoint: str = None, 
        api_key: str = None,
        api_version: str = None,
        deployment: str = None
    ):
        """
        Initialize the OpenAIAnalyzer.
        
        Args:
            endpoint: Azure OpenAI endpoint URL. If None, uses settings.
            api_key: Azure OpenAI API key. If None, uses settings.
            api_version: Azure OpenAI API version. If None, uses settings.
            deployment: Azure OpenAI deployment/model. If None, uses settings.
        """
        self.endpoint = endpoint or settings.azure_openai_endpoint
        self.api_key = api_key or settings.azure_openai_api_key
        self.api_version = api_version or settings.azure_openai_api_version
        self.deployment = deployment or settings.azure_openai_deployment
        self._client = None
    
    @property
    def client(self) -> AzureOpenAI:
        """
        Get the Azure OpenAI client.
        
        Returns:
            Initialized Azure OpenAI client.
        """
        if self._client is None:
            self._client = AzureOpenAI(
                api_version=self.api_version,
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
            )
        return self._client
    
    def test_connection(self) -> bool:
        """
        Test the OpenAI connection with a simple query.
        
        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            # First check if credentials are configured
            if not self.endpoint or not self.api_key:
                print("Azure OpenAI credentials are not configured")
                return False
            
            print("Testing OpenAI connection with a simple query...")
            test_response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say hello world."}
                ],
                model=self.deployment
            )
            print(f"Azure OpenAI test successful: {test_response.choices[0].message.content}")
            return True
        except Exception as e:
            print(f"Error testing Azure OpenAI connection: {str(e)}")
            return False
    
    def analyze_image(
        self, 
        image_path: str, 
        descriptions: List[str], 
        vision_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze an image using Azure OpenAI Vision.
        
        Args:
            image_path: Path to the image file.
            descriptions: List of possible food descriptions to match.
            vision_results: Optional Azure Vision results to guide analysis.
            
        Returns:
            Dictionary containing analysis results.
        """
        try:
            print(f"Processing image with OpenAI: {os.path.basename(image_path)}")
            
            # Encode the image to base64
            base64_image = encode_image_to_base64(image_path)
            print(f"Image encoded successfully: {len(base64_image)} characters")
            
            # Construct the prompt with all possible descriptions
            descriptions_for_prompt = '\n'.join(descriptions[:100])  # Limit to 100 items if list is very long

            # Build context from Azure Vision results if available
            vision_context = self._build_vision_context(vision_results) if vision_results else ""
            
            # Create the system prompt
            system_prompt = self._create_system_prompt()
            
            # Create the user prompt
            user_prompt = self._create_user_prompt(descriptions_for_prompt, vision_context)
            
            print("Sending image to OpenAI for analysis...")
            # Call the Azure OpenAI API with vision capabilities
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]}
                ],
                model=self.deployment
            )
            
            # Extract the description from the response
            description = response.choices[0].message.content.strip() if response.choices else ""
            print(f"OpenAI analysis complete: {len(description)} characters")
            
            current_filename = os.path.basename(image_path)
            
            return {
                "description": description,
                "file_name": current_filename
            }
        
        except Exception as e:
            print(f"Error analyzing image with OpenAI {image_path}: {str(e)}")
            current_filename = os.path.basename(image_path)
            
            return {
                "description": f"Error: {str(e)}",
                "file_name": current_filename
            }
    
    def _create_system_prompt(self) -> str:
        """
        Create the system prompt for OpenAI Vision.
        
        Returns:
            System prompt string.
        """
        return """
        You are a skilled visual analysis assistant specializing in food identification. Your role is to:
        1. Identify any text visible in the image that might identify the food
        2. Describe the primary food item shown clearly and accurately 
        3. Match the item to a menu description when reasonable, or mark as UNMATCHED if needed

        FOOD IDENTIFICATION GUIDELINES:
        - "Chicken Salad" is chopped/shredded chicken mixed with mayonnaise as a spread
        - A sandwich with chicken pieces/patty on bread/bun is a "Chicken Sandwich"
        - Breaded or fried chicken on a bun is a chicken sandwich
        - A burger has a ground meat patty; a sandwich has sliced meat or chicken pieces
        - A sub is on elongated roll/bun; a sandwich is typically on sliced bread or round bun
        - A wrap is in a tortilla/flatbread

        Your description should:
        - Report any text you can read in the image, prefixed with "TEXT DETECTED: "
        - Identify the food's category (sandwich, salad, burger, etc.)
        - Note key visual elements: bread type, filling/ingredients, preparation style
        
        When evaluating matches:
        - Use a balanced confidence scale (1-10) to indicate match quality
        - Don't be overly strict - use confidence scores to express uncertainty
        - For strong matches (8-10): The item clearly matches the description
        - For medium matches (5-7): The item generally matches with minor differences
        - For weak matches (1-4): The item has some similarity but significant differences
        - Mark as UNMATCHED when no reasonable match exists

        If uncertain, provide your best assessment with an appropriate confidence score that reflects your level of certainty.
        """
    
    def _create_user_prompt(self, descriptions_for_prompt: str, vision_context: str) -> str:
        """
        Create the user prompt for OpenAI Vision.
        
        Args:
            descriptions_for_prompt: List of possible food descriptions.
            vision_context: Vision API results context.
            
        Returns:
            User prompt string.
        """
        return f"""
        {vision_context}Identify and describe the food item in this image with precision. 

        IMPORTANT: First, carefully check for and read any text visible in the image (labels, packaging, price tags, etc.) that might identify the food item. Report this text exactly as written, prefixed with "TEXT DETECTED: ".
        
        Given the image I provide, your task is to:
        1. Look for and report any text visible in the image that might identify the food item
        2. Carefully analyze the visual features of the food
        3. Match the image to one of these menu item descriptions if possible:
        
        {descriptions_for_prompt}
        
        4. Provide a meaningful confidence score (1-10) that reflects how well the item matches:
           - Use 8-10 for very confident matches (clearly the same item)
           - Use 5-7 for possible matches with some uncertainty
           - Use 3-4 for items that have similarities but significant differences
           - Use 1-2 for very low confidence matches
        
        5. For items that don't clearly match any description, mark as UNMATCHED with a specific description:
           - Use ALL CAPS format
           - Create an abbreviated but descriptive name (e.g., CHK for chicken, SNDWCH for sandwich)
           - Example: "UNMATCHED FRIED CHKN SNDWCH" for an unmatched chicken sandwich
           - Still provide a confidence score (1-10) for your description of what the item is

        FOOD IDENTIFICATION GUIDELINES:
        - "Chicken Salad" refers to chopped/shredded chicken mixed with mayonnaise as a spread
        - A chicken patty on a bun is a "Chicken Sandwich" not "Chicken Salad"
        - A burger has a ground meat patty; a sandwich typically has whole meat
        - A sub is on elongated roll/bun; a sandwich is on sliced bread or round bun
        - A wrap is in a tortilla/flatbread; a burrito is a specific wrapped Mexican food
        - A salad plate has greens/vegetables as the base with toppings
        
        FORMAT YOUR RESPONSE AS:
        [Any detected text, prefixed with "TEXT DETECTED: "]
        [Best matching menu item OR your "UNMATCHED" description]
        [Confidence score: X/10]
        [Brief description of what you see, including key identifying features]
        """
    
    def _build_vision_context(self, vision_results: Dict[str, Any]) -> str:
        """
        Build context section based on Azure Vision results.
        
        Args:
            vision_results: Results from Azure Vision API.
            
        Returns:
            Formatted context string.
        """
        vision_context = "I'll provide you with Azure Vision API results for this image to help your analysis:\n\n"
        
        # Add caption information
        if vision_results["caption"]:
            vision_context += f"VISION API CAPTION: {vision_results['caption']} (Confidence: {vision_results['caption_confidence']:.2f})\n\n"
        
        # Add text detection information
        if vision_results["text"]:
            vision_context += "VISION API TEXT DETECTION:\n"
            for text_item in vision_results["text"]:
                if text_item["confidence"] > 0.5:  # Only include text with reasonable confidence
                    vision_context += f"- \"{text_item['text']}\" (Confidence: {text_item['confidence']:.2f})\n"
            vision_context += "\n"
        
        # Add tag information - focus on food-related tags
        food_related_tags = []
        if vision_results["tags"]:
            for tag in vision_results["tags"]:
                if tag["confidence"] > 0.7 and tag["name"] in [
                    "food", "sandwich", "bread", "burger", "meal", "lunch", "dinner", 
                    "breakfast", "plate", "meat", "cheese", "vegetable", "dessert", 
                    "salad", "wrap", "hamburger", "pasta", "pizza", "seafood", "rice", 
                    "chicken", "beef", "pork", "fish", "sauce", "condiment"
                ]:
                    food_related_tags.append(f"{tag['name']} (Confidence: {tag['confidence']:.2f})")
        
        if food_related_tags:
            vision_context += "VISION API FOOD-RELATED TAGS:\n- " + "\n- ".join(food_related_tags) + "\n\n"
        
        # Add object detection information
        if vision_results["objects"]:
            vision_context += "VISION API OBJECTS DETECTED:\n"
            for obj in vision_results["objects"]:
                vision_context += f"- {obj['name']} (Confidence: {obj['confidence']:.2f})\n"
            vision_context += "\n"
        
        vision_context += "INSTRUCTIONS FOR USING VISION API RESULTS:\n"
        vision_context += "1. Use the detected text as a strong signal for identifying the food item\n"
        vision_context += "2. Consider the Vision API caption as a helpful but not definitive description\n"
        vision_context += "3. Use the food-related tags to narrow down food categories\n"
        vision_context += "4. When the Vision API and your own analysis differ, prioritize what you can directly observe\n"
        vision_context += "5. Still be EXTREMELY STRICT about menu item matching\n\n"
        
        return vision_context


class AzureOpenAIService:
    """Service for Azure OpenAI image analysis."""

    def __init__(
        self, 
        endpoint: str = None, 
        api_key: str = None,
        api_version: str = None,
        deployment: str = None
    ):
        """
        Initialize the AzureOpenAIService.
        
        Args:
            endpoint: Azure OpenAI endpoint URL. If None, uses settings.
            api_key: Azure OpenAI API key. If None, uses settings.
            api_version: Azure OpenAI API version. If None, uses settings.
            deployment: Azure OpenAI deployment/model. If None, uses settings.
        """
        self.analyzer = OpenAIAnalyzer(
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            deployment=deployment
        )

    def is_available(self) -> bool:
        """
        Check if the Azure OpenAI service is available.
        
        Returns:
            True if available, False otherwise.
        """
        return self.analyzer.test_connection()

    def analyze_image(
        self, 
        image_path: str,
        descriptions: List[str],
        vision_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze an image using Azure OpenAI Vision.
        
        Args:
            image_path: Path to the image file.
            descriptions: List of possible food descriptions to match.
            vision_results: Optional Azure Vision results to guide analysis.
            
        Returns:
            Dictionary containing analysis results.
        """
        return self.analyzer.analyze_image(
            image_path=image_path,
            descriptions=descriptions,
            vision_results=vision_results
        )