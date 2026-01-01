#!/usr/bin/env python3
"""
Solar Panel Detection System - Main Entry Point

EcoInnovators Ideathon 2026 - Round 2
Team Akatsuki

Usage:
    python main.py

Configuration:
    Set environment variables in .env file:
    - GOOGLE_MAPS_API_KEY: Your Google Maps API key
    - MODEL_TYPE: 'bbox' or 'segmentation' (default: segmentation)
    - USE_SAHI: 'true' or 'false' (default: true)
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import SolarDetectionPipeline


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
    
    print(r"""
    ╔═══════════════════════════════════════════════════════════╗
    ║   ____        _              ____                  _      ║
    ║  / ___|  ___ | | __ _ _ __  |  _ \ __ _ _ __   ___| |___  ║
    ║  \___ \ / _ \| |/ _` | '__| | |_) / _` | '_ \ / _ \ / __| ║
    ║   ___) | (_) | | (_| | |    |  __/ (_| | | | |  __/ \__ \ ║
    ║  |____/ \___/|_|\__,_|_|    |_|   \__,_|_| |_|\___|_|___/ ║
    ║                                                           ║
    ║           Team Akatsuki - EcoInnovators 2026              ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    try:
        pipeline = SolarDetectionPipeline()
        pipeline.run()
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
