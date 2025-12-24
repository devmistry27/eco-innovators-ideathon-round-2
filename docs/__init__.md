# `__init__.py` - Package Initializer

## Overview

The `__init__.py` file serves as the entry point for the `src` package, defining the public API and metadata for the Solar Panel Detection System.

---

## Logic

```python
__version__ = "1.0.0"
__author__ = "Solar Detection Team"

from .pipeline import SolarDetectionPipeline
from .config import Config

__all__ = ['SolarDetectionPipeline', 'Config']
```

This module:
1. **Defines package metadata** - Version and author information
2. **Imports key classes** - Brings `SolarDetectionPipeline` and `Config` into the package namespace
3. **Controls public exports** - Uses `__all__` to specify what gets exported with `from src import *`

---

## How It Works

When Python imports the `src` package, it executes this `__init__.py` file. The relative imports (`.pipeline`, `.config`) tell Python to look for modules within the same package directory.

The `__all__` list defines the public interface, ensuring:
- Clean namespace for consumers
- IDE autocomplete suggestions
- Protection against accidental internal module exposure

---

## Why It Works

Python's import system requires an `__init__.py` (or implicit namespace packages in Python 3.3+) to recognize a directory as a package. By explicitly importing core classes:
- Users can write `from src import SolarDetectionPipeline` instead of `from src.pipeline import SolarDetectionPipeline`
- The package presents a clean, intentional API
- Internal implementation details remain hidden

---

## Usage in Main Pipeline

```python
# In main.py
from src.pipeline import SolarDetectionPipeline

# Could also use (thanks to __init__.py):
from src import SolarDetectionPipeline
```

The `__init__.py` enables:
- **Direct import access** - `main.py` can import `SolarDetectionPipeline` directly from `src`
- **Version checking** - External tools can access `src.__version__`
- **Module organization** - Establishes the package structure for the detection system
