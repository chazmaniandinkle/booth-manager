# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-02-24

### Added
- Initial release of Booth Assets Manager
- Flexible input file support (CSV, JSON, plain text)
- Automatic metadata scraping from Booth pages
- Image downloading and organization
- Centralized CSV database for item tracking
- Folder structure management
- Import and remove operations
- Force update option for re-downloading content
- Optional folder deletion during item removal
- Comprehensive error handling
- Case-insensitive key handling in input files
- SQLite database integration

### Features
- CSV parsing with URL/ID columns
- JSON file parsing with item objects
- Plain text file parsing (one item per line)
- Enhanced title extraction from meta tags
- Description capture from meta and content
- Image URL collection from multiple sources
- Automatic image downloading
- Subfolder creation and organization
- Skip existing files functionality
- Database management with CSV format
- Clear error messaging and recovery

### Technical
- Python 3.6+ compatibility
- Dependency management through setup.py
- Command-line interface implementation
- Network error handling
- File system error management
- Data consistency checks
- JSON serialization for arrays
- Path sanitization and validation
