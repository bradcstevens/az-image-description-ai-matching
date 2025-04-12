# Azure Image Description AI Matching - Project Planning

## Architecture Overview

This project uses a modular architecture to analyze food images and match them to menu descriptions using Azure AI services. It follows clean code practices, appropriate separation of concerns, and adheres to the SOLID principles.

## Design Goals

1. **Modularity**: Separate code into logical modules with clear responsibilities
2. **Testability**: Structure code to enable unit testing of individual components
3. **Configuration**: Allow flexible configuration via environment variables
4. **Error Handling**: Gracefully handle errors and provide useful messages
5. **Performance**: Optimize for processing large batches of images

## Module Structure

The project is organized into the following modules:

```
app/
├── config/           # Configuration
├── core/             # Core business logic
├── utils/            # Utility functions
└── tests/            # Unit tests
```

### Config Module

**Purpose**: Store application configuration and settings.

**Contents**:
- `settings.py`: Pydantic settings model for application configuration

### Core Module

**Purpose**: Implement the core business logic of the application.

**Contents**:
- `azure_openai.py`: Azure OpenAI integration for image analysis
- `azure_vision.py`: Azure Vision integration for image analysis
- `image_analyzer.py`: Main coordinator of image analysis and matching

### Utils Module

**Purpose**: Provide utility functions used across the application.

**Contents**:
- `file_utils.py`: File handling utilities (reading, writing, encoding)

### Tests Module

**Purpose**: Contain all unit tests for the application.

**Contents**:
- Unit tests for each module

## Dependency Management

- Use pydantic for configuration and type validation
- Use python-dotenv for environment variable loading
- Use pytest for unit testing

## Style Conventions

- Follow PEP8 and use Black for formatting
- Use Google-style docstrings for all functions and classes
- Use type hints for all functions and methods
- Organize imports in the following order:
  1. Standard library imports
  2. Third-party library imports
  3. Local application imports

## Error Handling Strategy

- Use try/except blocks to catch and handle specific exceptions
- Provide clear error messages
- Log errors with appropriate context
- Never suppress exceptions silently
- Return sensible defaults when operations fail

## Data Flow

1. Load configuration from environment variables
2. Initialize Azure services
3. Load descriptions from text file
4. For each image:
   a. Analyze with Azure Vision (if enabled)
   b. Analyze with Azure OpenAI (if enabled)
   c. Combine results
   d. Find best matching description
   e. Copy and rename image
5. Generate results summary

## Future Improvements

- Add asynchronous processing for better performance
- Implement a REST API for remote access
- Add a web interface for visualization
- Support more image formats beyond JPEG
- Add more sophisticated matching algorithms