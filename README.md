# Azure Image Description Matcher

This repository contains scripts for matching food images to menu descriptions using Azure AI services.

## Description

The application analyzes food images using Azure OpenAI and Azure AI Vision services to find the best matching description from a menu items list. It then renames and organizes the images based on their matching descriptions.

## Features

- Load food descriptions from a text file
- Analyze food images using Azure AI services
- Match images to the closest menu description
- Rename images based on their matched descriptions
- Organize results in timestamped folders for each run
- Generate a detailed JSON report of all matches

## Refactored Project Structure

This project has been refactored to follow a modular, maintainable architecture:

```
app/
├── config/           # Configuration
│   └── settings.py   # Pydantic settings model
├── core/             # Core business logic
│   ├── azure_openai.py   # Azure OpenAI integration
│   ├── azure_vision.py   # Azure Vision integration
│   └── image_analyzer.py # Main image analysis coordinator
├── utils/            # Utility functions
│   └── file_utils.py     # File handling utilities
└── tests/            # Unit tests
    ├── test_azure_openai.py
    ├── test_azure_vision.py
    ├── test_file_utils.py
    └── test_image_analyzer.py
```

### Key Features:

* **Modular Design**: Clear separation of concerns with focused modules
* **Service Architecture**: Each Azure service has its own dedicated class
* **Dependency Injection**: Services can be injected for better testability 
* **Error Handling**: Robust error handling throughout the codebase
* **Testing**: Comprehensive unit tests with pytest

## Prerequisites

- Python 3.8 or later
- Azure subscription with access to:
  - Azure OpenAI (optional)
  - Azure Computer Vision (optional)

## Setup

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your API credentials:

```
# For Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-openai-api-key
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# For Azure AI Vision
AZURE_VISION_ENDPOINT=https://your-vision-resource.cognitiveservices.azure.com/
AZURE_VISION_KEY=your-vision-api-key
```

3. Create a `food-descriptions.txt` file with your menu items, one per line:

```
Margherita Pizza with Fresh Basil
Chicken Caesar Salad with Croutons
Chocolate Lava Cake with Vanilla Ice Cream
...
```

4. Place your food images in an `images` directory (JPEG format)

## Usage

You can run the application using:

```bash
python run.py
```

By default, it will:
1. Read food descriptions from `food-descriptions.txt`
2. Process all JPEG images in the `images/` directory
3. Save results to a timestamped directory in `results/`

### Command Line Arguments

The application supports several command-line arguments:

```
--images-dir DIR      Directory containing images
--results-dir DIR     Directory to store results
--descriptions-file FILE  File with descriptions
--use-openai BOOL     Use Azure OpenAI for analysis
--use-vision BOOL     Use Azure Vision for analysis
--image-pattern PATTERN  Glob pattern for images (default: *.jpeg)
```

Example:
```bash
python run.py --images-dir custom_images --descriptions-file custom_descriptions.txt
```

## Output

The application will:

1. Create a timestamped folder in the `results` directory
2. Save copies of the analyzed images with filenames based on the matched description
3. Generate a JSON file with detailed analysis results
4. Display a summary of matches in the console

## Development

### Setting Up a Development Environment

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in your Azure API keys

### Running Tests

```bash
pytest
```

Or to run tests with coverage:

```bash
pytest --cov=app
```

## Troubleshooting

If you encounter issues:

1. Verify your API keys and endpoints in the `.env` file
2. Ensure your images are in JPEG format and located in the `images` directory
3. Check that your descriptions.txt file exists and contains menu items 