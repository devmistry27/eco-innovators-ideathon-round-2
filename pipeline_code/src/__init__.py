"""
Solar Panel Detection System - Package exports.
"""

from .config import AppConfig as Config
from .pipeline import SolarDetectionPipeline
from .detector import SolarDetector
from .visualizer import Visualizer

__all__ = [
    'Config',
    'SolarDetectionPipeline', 
    'SolarDetector',
    'Visualizer'
]

__version__ = '2.0.0'
