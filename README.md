# Booth Assets Manager

[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python tool to manage and organize Booth item assets. This package lets you import items by reading a CSV (with "URL" or "ID" columns), JSON, or plain text file containing Booth item links or IDs. It can scrape metadata, download preview images, and now with the new authentication system, **download your purchased items directly**. It also supports integration with VRChat Creator Companion (VCC) to allow you to use your Booth assets directly in Unity projects.

## New in v0.4.0: Graphical User Interface

The latest version adds a comprehensive GUI for easier interaction:

- **Modern Interface**: Intuitive tabbed interface with Dashboard, Items, Downloads, VCC Integration, and Settings
- **Visual Management**: Browse, search, and filter your items with a visual interface
- **Interactive Downloads**: Track download progress visually and manage your purchases
- **VCC Management**: Package and manage your VCC repository with a few clicks
- **Multithreaded Operations**: Background processing keeps the interface responsive

![Booth Assets Manager GUI](https://github.com/chazmaniandinkle/booth-assets-manager/raw/main/docs/images/gui-screenshot.png)

## Also in v0.3.0: Download Your Purchased Items

- **Interactive Browser Authentication**: Log in through a browser window that opens from the app
- **Purchase Management**: List and track your Booth purchases
- **Direct Downloads**: Download purchased item files directly through the application
- **Automated Organization**: Files are automatically organized into your asset structure

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [GUI Interface](#gui-interface)
  - [Importing Items](#importing-items)
  - [Removing Items](#removing-items)
  - [Authentication](#authentication)
  - [Downloading Purchases](#downloading-purchases)
  - [VCC Integration](#vcc-integration)
- [Input File Formats](#input-file-formats)
- [Database](#database)
- [VCC Repository](#vcc-repository)
- [How It Works](#how-it-works)
- [Extending the Script](#extending-the-script)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- **Graphical User Interface:**
  - Dashboard with statistics and quick actions
  - Items management with search and filtering
  - Visual download management with progress tracking
  - VCC integration interface with repository management
  - Settings configuration panel
  - Multithreaded operations for background tasks

- **Flexible Input:**  
  Accepts CSV, JSON, or plain text files with Booth URLs or item IDs.

- **Automatic Metadata Scraping:**  
  Scrapes key metadata from Booth pages, including title, item ID, description, and image URLs.

- **Image Capture & Download:**  
  Downloads preview images found on the item page.

- **Folder Organization:**  
  Creates a dedicated folder for each item under the `BoothItems` directory.

- **Centralized Database:**  
  Maintains a SQLite database that stores metadata and relationships for all managed items.

- **Authentication:**
  - Interactive browser-based login
  - Secure cookie storage
  - Session management
  - Session validation

- **Purchase Management:**
  - List purchased items
  - Track purchase details
  - Update database with purchase information

- **Download Features:**
  - Direct download of purchased items
  - Progress tracking
  - Parallel downloads with concurrency control
  - Resumable downloads
  - File integrity verification
  - Automatic organization

- **VCC Integration:**  
  Create VRChat Creator Companion compatible packages from your Booth assets.
  - Generate Unity package structure from Booth assets
  - Create local VCC repository
  - Add repository to VCC with a single click
  - Auto-package new items as they're downloaded

---

## Prerequisites

- **Python 3.6+**
- **Required Packages:**  
  - `requests`, `beautifulsoup4`, `sqlalchemy` (Base functionality)
  - `playwright`, `tqdm` (Authentication and downloads)
  - `PyQt6` (GUI interface)

These are automatically installed when you install the package.

---

## Installation

1. **Clone or Download the Repository**

   ```bash
   git clone https://github.com/chazmaniandinkle/booth-assets-manager.git
   cd booth-assets-manager
   ```

2. **Install the Package**
   You can install the package in editable mode (for development) with pip:

   ```bash
   pip install -e .
   ```

   Alternatively, build and install using:

   ```bash
   python setup.py sdist bdist_wheel
   pip install dist/booth_assets_manager-0.3.0-py3-none-any.whl
   ```

3. **Install Browser Dependencies**

   The authentication system uses Playwright which requires browser binaries:

   ```bash
   playwright install
   ```

---

## Usage

Once installed, the tool provides four command-line scripts: `booth-gui` for the graphical interface, `booth-assets-manager` for general operations, `booth-vcc` for VCC integration, and `booth-auth` for authentication and downloads.

### GUI Interface

To launch the graphical interface:

```bash
booth-gui
```

The GUI provides access to all functionality through a user-friendly interface:

- **Dashboard**: Shows statistics and quick actions
- **Items**: Browse, search, and manage your Booth items
- **Downloads**: Authenticate with Booth, view purchases, and download files
- **VCC Integration**: Enable/disable VCC features, package items, and manage repositories
- **Settings**: Configure paths, VCC parameters, and download options

### Importing Items

To import items from an input file and update your local database, run:

```bash
booth-assets-manager input_file [--force]
```

- `input_file`: Path to your CSV, JSON, or plain text file.
- `--force`: Optional flag to force re-download of metadata and images even if already present.

Example:

```bash
booth-assets-manager my_items.csv --force
```

### Removing Items

To remove items from your database (and optionally delete their folders), run:

```bash
booth-assets-manager input_file --remove [--delete-folders]
```

- `input_file`: Path to your CSV, JSON, or plain text file listing items to remove.
- `--delete-folders`: Optional flag to also delete the associated item folders from disk.

Example:

```bash
booth-assets-manager remove_items.txt --remove --delete-folders
```

### Authentication

To authenticate with Booth and enable direct downloads:

```bash
# Start interactive login
booth-auth login

# Check authentication status
booth-auth status

# Log out and clear session data
booth-auth logout
```

The login command will open a browser window where you can log in to your Booth account. Once logged in, the window will close automatically and your session will be saved for future use.

### Downloading Purchases

To download your purchased items:

```bash
# List purchases and optionally update database
booth-auth purchases [--update-db]

# Download a specific item
booth-auth download --item-id ITEM_ID

# Download all purchased items
booth-auth download --all

# Specify output directory
booth-auth download --all --output-dir /path/to/directory

# Control concurrent downloads
booth-auth download --all --concurrent 5
```

Downloaded files are organized into a folder structure similar to the main item structure:

```
BoothDownloads/
├── {item_id}_{title}/
│   ├── downloads/
│   │   ├── file1.zip
│   │   └── file2.pdf
│   └── extracted/
│       └── file1/
```

### VCC Integration

You can use VCC integration to create Unity packages:

```bash
# Enable VCC integration
booth-vcc enable

# Package all items
booth-vcc package-all

# Add repository to VCC
booth-vcc add-to-vcc
```

---

## Input File Formats

### CSV Files

```csv
URL,Title
https://booth.pm/items/123456789,Stylish Outfit
https://booth.pm/items/987654321,Cool Jacket
```

Or using IDs:
```csv
ID,Title
123456789,Stylish Outfit
987654321,Cool Jacket
```

### JSON Files

```json
[
  {
    "url": "https://booth.pm/items/123456789",
    "title": "Stylish Outfit"
  },
  {
    "id": "987654321",
    "title": "Cool Jacket"
  }
]
```

### Plain Text Files

```
https://booth.pm/items/123456789
987654321
```

---

## Database

The tool uses a SQLite database (`booth.db`) with SQLAlchemy ORM. The extended schema includes:

### Items Table
- Basic metadata (item_id, title, url, description, etc.)
- Purchase information (is_purchased, purchase_date, purchase_price, etc.)
- Package information for VCC integration
- Download status tracking

### Images Table
- Original image URLs and local paths
- Relationship to parent item

### Downloads Table
- Downloaded file information
- File paths and download status
- File integrity information
- Download history tracking

The database is automatically created on first run and maintains relationships between items, images, and downloads. All operations use transactions to ensure data consistency.

---

## VCC Repository

The VCC integration creates a local repository that can be added to the VRChat Creator Companion. The repository structure follows the VCC format:

```
Repository/
├── index.json            # Repository listing
└── Packages/             # Package storage
    ├── com.creator.item1/
    │   ├── package.json  # Package manifest
    │   ├── README.md     # Generated from item description
    │   ├── Runtime/      # Asset files
    │   └── Documentation~/ # Images and documentation
    └── com.creator.item2/
        └── ...
```

---

## How It Works

### Item Import Process
1. The tool reads your input file, determining whether each entry is a URL or an ID.
2. For each item, a dedicated folder is created under `BoothItems/`.
3. The tool scrapes the item's metadata from Booth.
4. Images are downloaded into an `images` subfolder.
5. The collected metadata is stored in the SQLite database.
6. If VCC integration is enabled, a Unity package is created.

### Authentication Process
1. When you run `booth-auth login`, a browser window opens.
2. You log into your Booth account normally in this window.
3. Once logged in, the application automatically captures the authentication cookies.
4. These cookies are securely stored for future sessions.
5. The browser window closes automatically after successful login.

### Download Process
1. When you list purchases, the tool uses your authentication to access your Booth account.
2. For each purchased item, it extracts the title, ID, purchase date, and price.
3. When downloading, it visits the item's download page to extract download links.
4. Files are downloaded with progress tracking and organized into folders.
5. Download information is stored in the database for tracking.
6. If VCC integration is enabled, downloaded items can be packaged for Unity.

---

## Extending the Script

Future enhancements might include:
- Enhanced metadata extraction (e.g., additional tags or compatibility information).
- Automatic detection of asset updates for VCC packages.
- Dependency management between packages.
- Direct VCC project integration.
- Custom package templates for different asset types.
- Additional GUI features and visualizations.
- Configuration file support for persistent settings.

Feel free to modify or extend the code to suit your workflow.

---

## Troubleshooting

### General Issues
- **Metadata Scraping Errors:**
  If metadata isn't being scraped correctly, verify that the CSS selectors match Booth's current page structure.

- **Input Parsing Issues:**
  Ensure your input file is formatted correctly. For CSV and JSON files, use the proper keys ("url" or "id").

- **Network Errors:**
  Verify your internet connection if the tool fails to retrieve pages.

### GUI Issues
- **GUI doesn't start:**
  Ensure PyQt6 is properly installed. Try reinstalling with `pip install PyQt6`.

- **Slow performance:**
  The GUI uses multithreading for background tasks, but very large operations might still cause temporary UI freezes.

- **Display issues:**
  If you encounter display problems, try adjusting your system's scaling settings or update your graphics drivers.

### Authentication Issues
- **Browser doesn't open:**
  Ensure Playwright is properly installed with `playwright install`.

- **Login timeout:**
  The default timeout is 5 minutes. Try again if needed.

- **Session expires:**
  Sessions will eventually expire. Use the login button to reauthenticate.

### Download Issues
- **Download failures:**
  Check your internet connection and Booth account status.

- **Parallel download errors:**
  Reduce the concurrency in the settings tab if you encounter issues.

- **Large file downloads:**
  Ensure you have sufficient disk space for large downloads.

### VCC Integration Issues
- If VCC doesn't recognize the repository, check that the repository path is correct.
- If the vcc:// protocol link doesn't work, try adding the repository manually in VCC.
- If packages don't appear in Unity, verify that the package structure is correct.

---

## License

This project is licensed under the MIT License.
