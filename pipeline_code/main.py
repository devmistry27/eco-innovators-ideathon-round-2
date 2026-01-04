#!/usr/bin/env python3
"""
Solar Panel Detection System - Main Entry Point

EcoInnovators Ideathon 2026 - Round 2
Team Akatsuki

Usage:
    python main.py --input <path_to_input.xlsx> --output <output_folder_path>

Configuration:
    Set environment variables in .env file:
    - GOOGLE_MAPS_API_KEY: Your Google Maps API key
    - MODEL_PATH: Path to YOLO model
"""

import logging
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add src to path for imports if needed
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import SolarDetectionPipeline

# Load environment variables
load_dotenv()

def setup_logging():
    """Configure logging format."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )


def main():
    """Main entry point."""
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Solar Panel Detection Pipeline")
    parser.add_argument('--input', type=str, default=None, help='Path to input Excel file')
    parser.add_argument('--output', type=str, default=None, help='Path to output folder')
    
    args = parser.parse_args()
    
    print("Starting Solar Panel Detection Pipeline...")
    
    try:
        pipeline = SolarDetectionPipeline()
        pipeline.run(input_file=args.input, output_folder=args.output)
        
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
