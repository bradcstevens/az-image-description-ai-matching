#!/usr/bin/env python3
"""
Main script for Azure Image Description AI Matching application.
"""
import os
import glob
from tqdm import tqdm
import argparse
import json
import shutil
import subprocess
import sys

from app.config.settings import settings
from app.core.azure_openai import AzureOpenAIService
from app.core.azure_vision import AzureVisionService
from app.core.image_analyzer import ImageAnalyzer
from app.utils.file_utils import (
    load_descriptions_from_file,
    create_timestamped_directory,
    ensure_directory_exists,
    validate_image_file
)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Azure Image Description AI Matching"
    )
    parser.add_argument(
        "--images-dir",
        type=str,
        default=settings.images_dir,
        help=f"Directory containing images (default: {settings.images_dir})"
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default=settings.results_base_dir,
        help=f"Directory to store results (default: {settings.results_base_dir})"
    )
    parser.add_argument(
        "--descriptions-file",
        type=str,
        default=settings.food_descriptions_file,
        help=f"File with descriptions (default: {settings.food_descriptions_file})"
    )
    parser.add_argument(
        "--image-pattern",
        type=str,
        default="*.jpeg",
        help="Glob pattern for images (default: *.jpeg)"
    )
    parser.add_argument(
        "--allow-single-service",
        action="store_true",
        help="Continue if only one of the AI services is available"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=0,
        help="Process only a sample of N images (default: process all)"
    )
    return parser.parse_args()


def run_git_lfs_pull():
    """
    Attempt to run git lfs pull to retrieve actual images.
    
    Returns:
        Tuple of (success, message) where success is a boolean indicating if the
        command was successful, and message is any error message if not.
    """
    try:
        # First check if git lfs is installed
        subprocess.run(["git", "lfs", "--version"], 
                     check=True, 
                     stdout=subprocess.PIPE, 
                     stderr=subprocess.PIPE)
        
        # Run git lfs pull
        result = subprocess.run(["git", "lfs", "pull"], 
                             check=True, 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE)
        
        return True, f"Successfully pulled LFS files: {result.stdout.decode('utf-8')}"
    except subprocess.CalledProcessError as e:
        return False, f"Git LFS command failed: {e.stderr.decode('utf-8')}"
    except FileNotFoundError:
        return False, "Git LFS is not installed on your system"
    except Exception as e:
        return False, f"Unexpected error running Git LFS: {str(e)}"


def main():
    """Main entry point for the application."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Create a timestamped results directory
    results_dir = create_timestamped_directory(args.results_dir)
    print(f"Results will be saved to: {results_dir}")
    
    # Validate OpenAI service
    print("Validating Azure OpenAI service...")
    openai_service = AzureOpenAIService()
    openai_available = openai_service.is_available()
    if openai_available:
        print("✓ Azure OpenAI service is available")
    else:
        print("✗ Azure OpenAI service is NOT available - check your API key and endpoint")
        
    # Validate Vision service
    print("Validating Azure Vision service...")
    vision_service = AzureVisionService()
    vision_available = vision_service.is_available()
    if vision_available:
        print("✓ Azure Vision service is available")
    else:
        print("✗ Azure Vision service is NOT available - check your API key and endpoint")
    
    # Check if at least one service is available
    if not openai_available and not vision_available:
        print("Error: No image analysis services available. Please check your credentials.")
        return
    
    # If both services are available, or if only one is available and --allow-single-service is set
    if (openai_available and vision_available) or args.allow_single_service:
        if openai_available and vision_available:
            print("Both Azure OpenAI and Vision services are available and will be used together for optimal results.")
        elif openai_available:
            print("Only Azure OpenAI service is available. Vision features (tags, object detection) will be disabled.")
            print("This may reduce matching accuracy for some images.")
        elif vision_available:
            print("Only Azure Vision service is available. Advanced matching capabilities will be reduced.")
            print("This will significantly reduce matching accuracy.")
        
        # Load descriptions
        descriptions = load_descriptions_from_file(args.descriptions_file)
        if not descriptions:
            print(f"Error: No descriptions found in {args.descriptions_file}")
            return
        
        # Create image analyzer with available services
        image_analyzer = ImageAnalyzer(
            openai_service=openai_service if openai_available else None,
            vision_service=vision_service if vision_available else None,
            descriptions=descriptions
        )
        
        # Get all images matching the pattern
        image_pattern = os.path.join(args.images_dir, args.image_pattern)
        image_paths = glob.glob(image_pattern)
        
        if not image_paths:
            print(f"No images found matching pattern {image_pattern}")
            return
        
        # Check for Git LFS pointers and provide warning
        lfs_pointer_count = 0
        for image_path in image_paths[:5]:  # Check first few files
            is_valid, _ = validate_image_file(image_path)
            if not is_valid:
                lfs_pointer_count += 1
        
        if lfs_pointer_count > 0:
            print("\n⚠️ Detected Git LFS pointer files instead of actual images.")
            print("Attempting to automatically pull LFS files...")
            
            # Try to run git lfs pull automatically
            success, message = run_git_lfs_pull()
            
            if success:
                print(f"✓ {message}")
                print("Checking if images are now properly downloaded...")
                
                # Recheck the same files to see if they're now valid
                lfs_pointer_count_after = 0
                for image_path in image_paths[:5]:
                    is_valid, _ = validate_image_file(image_path)
                    if not is_valid:
                        lfs_pointer_count_after += 1
                
                if lfs_pointer_count_after == 0:
                    print("✓ Successfully downloaded all LFS images!")
                else:
                    print(f"⚠️ There are still {lfs_pointer_count_after} LFS pointer files.")
                    show_lfs_instructions()
                    
                    # Ask for confirmation to continue
                    if input("Continue anyway? (y/n): ").lower() != 'y':
                        print("Exiting at user request.")
                        return
            else:
                print(f"✗ {message}")
                show_lfs_instructions()
                
                # Ask for confirmation to continue
                if input("Continue anyway? (y/n): ").lower() != 'y':
                    print("Exiting at user request.")
                    return
        
        # Limit to a sample if specified
        if args.sample > 0 and args.sample < len(image_paths):
            print(f"Limiting to a sample of {args.sample} images")
            # Take a sample from evenly distributed indices
            step = len(image_paths) // args.sample
            image_paths = image_paths[::step][:args.sample]
        
        print(f"Found {len(image_paths)} images to analyze.")
        print(f"Using {len(descriptions)} menu item descriptions from {args.descriptions_file}.")
        
        # Process each image
        results = []
        invalid_image_count = 0
        for image_path in tqdm(image_paths, desc="Analyzing images"):
            # Validate the image file first
            is_valid, error_message = validate_image_file(image_path)
            if not is_valid:
                print(f"Skipping invalid image {image_path}: {error_message}")
                invalid_image_count += 1
                # Add a minimal error result
                results.append({
                    "file_name": os.path.basename(image_path),
                    "error": error_message
                })
                continue
            
            # Analyze the image
            try:
                analysis_result = image_analyzer.analyze_image(image_path)
                
                # Add the result to our list
                results.append(analysis_result)
                
                # Save the matched image with its new name
                if analysis_result.get("match"):
                    # Copy the image with the matched description name
                    result_filename = analysis_result.get("match_filename") or analysis_result.get("filename")
                    source_path = image_path
                    target_path = os.path.join(results_dir, result_filename)
                    try:
                        shutil.copy2(source_path, target_path)
                    except Exception as e:
                        print(f"Error copying image {source_path} to {target_path}: {str(e)}")
            except Exception as e:
                print(f"Error analyzing image {image_path}: {str(e)}")
                # Add minimal error result
                results.append({
                    "file_name": os.path.basename(image_path),
                    "error": str(e)
                })
        
        # Save the results as JSON
        results_json_path = os.path.join(results_dir, "results.json")
        with open(results_json_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to {results_json_path}")
        
        # Print summary statistics
        matched_count = sum(1 for r in results if r.get("match") and not r.get("match", "").startswith("UNMATCHED"))
        unmatched_count = len(results) - matched_count - invalid_image_count
        
        print(f"\nAnalysis complete!")
        print(f"Total images processed: {len(results)}")
        print(f"Invalid images (skipped): {invalid_image_count}")
        print(f"Matched items: {matched_count}")
        print(f"Unmatched items: {unmatched_count}")
        if len(results) > invalid_image_count:
            print(f"Match rate: {matched_count / (len(results) - invalid_image_count) * 100:.1f}%")
        
        # Add Git LFS reminder if there were invalid images
        if invalid_image_count > 0:
            print("\n⚠️ REMINDER: Some images were Git LFS pointers, not actual images.")
            print("To get the actual images, run: git lfs pull")
    else:
        print("Both services are required unless --allow-single-service is specified.")
        print("Run with --allow-single-service to use only the available service(s).")


def show_lfs_instructions():
    """Display instructions for setting up Git LFS."""
    print("\nTo fix this issue manually, you need to:")
    print("1. Install Git LFS if you haven't already:")
    print("   - macOS: brew install git-lfs")
    print("   - Windows: https://git-lfs.github.com/")
    print("   - Linux: apt-get install git-lfs or equivalent")
    print("2. Initialize Git LFS: git lfs install")
    print("3. Pull the actual files: git lfs pull")
    print("\nProceeding will likely result in errors for these files.\n")


if __name__ == "__main__":
    main() 