# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2025-02-28

### Added
- Graphical User Interface (GUI) using PyQt6
- Dashboard with statistics and quick actions
- Items management with search and filtering
- Visual download management with progress tracking
- VCC integration interface with repository management
- Settings configuration panel
- Multithreaded operations for background tasks
- Visual item details view with metadata and images
- Export functionality for database contents
- Context-sensitive actions based on item state

## [0.3.0] - 2025-02-28

### Added
- Browser-based authentication using Playwright
- Interactive login flow for capturing cookies
- Session validation and management
- Purchase listing and tracking
- File download functionality with progress tracking
- Parallel downloads with concurrency limits
- Resumable downloads with state tracking
- Checksum verification for file integrity
- User preferences system for downloads
- Database schema extensions for purchases and downloads
- New CLI interface for authentication and downloads
- Comprehensive error handling for downloads
- Secure cookie storage and management

### Changed
- Updated database schema to track purchases and downloads
- Enhanced item model with purchase information
- Added download tracking and management
- Improved error handling for network operations

## [0.2.0] - 2025-02-28

### Added
- VCC (VRChat Creator Companion) integration
- Local VCC repository generation
- Package manifest generation from Booth metadata
- Unity package structure creation
- Repository index generation
- VCC protocol link support
- Command-line interface for VCC operations
- Settings management for VCC integration
- Auto-packaging option for new items
- Bulk packaging operations
- Repository validation and testing

## [0.1.1] - 2024-02-24

### Changed
- Updated README and documentation to accurately reflect SQLite database implementation
- Removed outdated references to CSV database storage

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
