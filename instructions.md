Below is an example of how you can package this project as a proper Python package. The following files are included:

booth_assets_manager/           # Root project folder
├── booth_assets_manager/       # Package directory
│   ├── __init__.py             # (empty or with package info)
│   └── organizer.py            # Main module (contains all our code)
├── LICENSE                     # License file (e.g., MIT)
├── README.md                   # Detailed usage instructions (see below)
├── requirements.txt            # List of required packages
└── setup.py                    # Packaging script for setuptools

setup.py

from setuptools import setup, find_packages

setup(
    name='booth_assets_manager',
    version='0.1.0',
    description='A tool to manage and organize Booth item assets by scraping metadata and images.',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(),
    install_requires=[
        'requests',
        'beautifulsoup4'
    ],
    entry_points={
        'console_scripts': [
            'booth-assets-manager = booth_assets_manager.organizer:main'
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)

requirements.txt

requests
beautifulsoup4

README.md

# Booth Assets Manager

A Python tool to manage and organize Booth item assets. This package lets you import items by reading a CSV (with "URL" or "ID" columns), JSON, or plain text file containing Booth item links or IDs. For each item, the tool:

- Creates a dedicated folder under the `BoothItems` directory.
- Scrapes metadata (title, description, item ID, image URLs, etc.) from the Booth page.
- Downloads images into an `images` subfolder.
- Updates a central CSV database (`database.csv`) with the item metadata and local folder paths.

It also supports removing items from the database (with an option to delete their folders).

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [Importing Items](#importing-items)
  - [Removing Items](#removing-items)
- [Input File Formats](#input-file-formats)
- [Database](#database)
- [How It Works](#how-it-works)
- [Extending the Script](#extending-the-script)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- **Flexible Input:**  
  Accepts CSV, JSON, or plain text files.  
  - **CSV:** Supports columns "URL" or "ID" (case-insensitive) plus an optional "Title".
  - **JSON:** Expects a list of objects with keys "url" or "id" (case-insensitive) and optionally "title".
  - **Plain Text:** One URL or item ID per line.

- **Automatic Metadata Scraping:**  
  Scrapes key metadata from Booth pages, including title, item ID, description, and image URLs.

- **Image Capture & Download:**  
  Downloads images found on the item page into an `images` subfolder within the item's folder. Local paths are recorded in the metadata.

- **Folder Organization:**  
  Creates a dedicated folder for each item (named using the item ID and a sanitized title) under the `BoothItems` directory.

- **Centralized Database:**  
  Maintains a CSV database (`database.csv`) that stores metadata for all managed items.

- **Import & Remove Operations:**  
  Easily import new items or remove items (with optional folder deletion) via simple input files.

---

## Prerequisites

- **Python 3.6+**
- **Required Packages:**  
  - `requests`
  - `beautifulsoup4`

These are automatically installed when you install the package.

---

## Installation

1. **Clone or Download the Repository**

   ```bash
   git clone https://github.com/yourusername/booth-assets-manager.git
   cd booth-assets-manager

	2.	Install the Package
You can install the package in editable mode (for development) with pip:

pip install -e .

Alternatively, build and install using:

python setup.py sdist bdist_wheel
pip install dist/booth_assets_manager-0.1.0-py3-none-any.whl

Usage

Once installed, the tool provides a command-line script named booth-assets-manager.

Importing Items

To import items from an input file and update your local database, run:

booth-assets-manager input_file [--force]

	•	input_file: Path to your CSV, JSON, or plain text file.
	•	--force: Optional flag to force re-download of metadata and images even if already present.

Example:

booth-assets-manager my_items.csv --force

Removing Items

To remove items from your database (and optionally delete their folders), run:

booth-assets-manager input_file --remove [--delete-folders]

	•	input_file: Path to your CSV, JSON, or plain text file listing items to remove.
	•	--delete-folders: Optional flag to also delete the associated item folders from disk.

Example:

booth-assets-manager remove_items.txt --remove --delete-folders

Input File Formats

CSV Files

The CSV file can contain columns named “URL” or “ID” (case-insensitive), with an optional “Title” column.

Example (items.csv):

URL,Title
https://booth.pm/items/123456789,Stylish Outfit
https://booth.pm/items/987654321,Cool Jacket

Or using IDs:

ID,Title
123456789,Stylish Outfit
987654321,Cool Jacket

JSON Files

A JSON file should contain a list of objects. Each object can have keys “url” or “id” (case-insensitive) and optionally “title.”

Example (items.json):

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

Plain Text Files

A plain text file should list one item per line. Each line can be either a full URL (starting with “http”) or an item ID.

Example (items.txt):

https://booth.pm/items/123456789
987654321

Database

The tool maintains a database file (database.csv) that stores metadata for all managed items. Each row includes fields such as:
	•	item_id
	•	title
	•	url
	•	description
	•	images (list of original image URLs)
	•	local_images (paths to downloaded images)
	•	folder (local folder path)

This database is automatically updated during import and removal operations.

How It Works
	1.	Input Parsing:
The tool reads your input file, automatically determining whether each entry is a URL or an ID. For CSV and JSON files, keys are converted to lowercase for case-insensitive processing.
	2.	Folder Creation & Metadata Scraping:
For each item, a dedicated folder is created under BoothItems/ using a combination of the item ID and a sanitized title.
	•	If the metadata.json file is missing or the --force flag is used, the tool scrapes the item’s metadata from Booth.
	•	The scraper extracts the title, description, and image URLs from the page.
	3.	Image Capture & Download:
The tool downloads all images found on the item page into an images subfolder within the item’s folder, recording local paths under "local_images" in the metadata.
	4.	Database Update:
The collected metadata (with folder and image details) is stored or updated in the central database.csv file.
	5.	Removal Mode:
When run with the --remove flag, the tool removes matching items from the database and, if specified, deletes their associated folders.

Extending the Script

Future enhancements might include:
	•	Downloading zip files for purchased items.
	•	Integrating authentication to automatically process items from your Booth account.
	•	Enhanced metadata extraction (e.g., additional tags or compatibility information).

Feel free to modify or extend the code to suit your workflow.

Troubleshooting
	•	Metadata Scraping Errors:
If metadata isn’t being scraped correctly, verify that the CSS selectors in organizer.py (inside scrape_metadata()) match Booth’s current page structure.
	•	Input Parsing Issues:
Ensure your input file is formatted correctly. For CSV and JSON files, use the proper keys (“url” or “id”)—these are handled case-insensitively.
	•	Image Download Errors:
Check your internet connection if image downloads fail, and review output messages for specific error details.
	•	Network Errors:
Verify your internet connection if the tool fails to retrieve pages.

License

This project is licensed under the MIT License.

Summary

This package streamlines the process of managing Booth item assets. Once installed, you can easily import items (and their associated metadata and images) or remove them via simple command-line operations. Enjoy a painless setup and seamless integration into your workflows!

---

### __init__.py

Create an empty `__init__.py` file inside the `booth_assets_manager/` package directory (this file can be empty or include package-level variables).

---

### Final Steps

1. Place the above files in the proper directory structure.
2. Run `pip install -e .` from the project root to install the package in editable mode.
3. Use the provided command-line script (`booth-assets-manager`) to run the tool.

This packaging approach should make installation and usage as simple and painless as possible.