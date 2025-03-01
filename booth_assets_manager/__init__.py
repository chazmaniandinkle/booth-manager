"""
Booth Assets Manager - A tool to manage and organize Booth item assets.

This package provides functionality to:
- Import items from Booth marketplace
- Scrape metadata and download images
- Organize assets into a consistent folder structure
- Store metadata in a SQLite database
- Create VRChat Creator Companion (VCC) packages from Booth assets
"""

__version__ = '0.2.0'

from .database import Database
from .settings import settings
