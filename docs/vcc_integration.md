# VCC Integration Guide

This guide explains how to use the VRChat Creator Companion (VCC) integration feature of the Booth Assets Manager.

## Overview

The VCC integration allows you to create Unity packages from your Booth assets and make them available in the VRChat Creator Companion. This makes it easy to use your Booth assets directly in Unity projects.

## Features

- Create Unity packages from Booth assets
- Generate a local VCC repository
- Add the repository to VCC with a single click
- Auto-package new items as they're downloaded
- Manage packages through a dedicated CLI

## Getting Started

### 1. Enable VCC Integration

First, enable the VCC integration:

```bash
booth-vcc enable
```

This will:
- Create the repository directory structure
- Generate an initial repository index
- Enable VCC integration in the settings

### 2. Package Your Assets

You can package all your existing Booth assets:

```bash
booth-vcc package-all
```

Or package a specific item:

```bash
booth-vcc package ITEM_ID
```

### 3. Add Repository to VCC

To add your repository to VCC:

```bash
booth-vcc add-to-vcc
```

This will open a VCC protocol link in your browser, which will prompt VCC to add your repository.

## Command Reference

The `booth-vcc` command provides several subcommands:

- `enable`: Enable VCC integration
- `disable`: Disable VCC integration
- `package ITEM_ID`: Package a specific item
- `unpackage ITEM_ID`: Remove a package
- `package-all`: Package all items
- `regenerate`: Regenerate repository index
- `add-to-vcc`: Add repository to VCC
- `validate`: Validate repository structure
- `status`: Show repository status
- `settings`: Show or update settings

### Settings Management

You can view and update settings:

```bash
booth-vcc settings
```

To update specific settings:

```bash
booth-vcc settings --repository-path /path/to/repo
booth-vcc settings --repository-name "My Booth Assets"
booth-vcc settings --repository-id "com.myname.boothAssets"
booth-vcc settings --repository-author "your@email.com"
booth-vcc settings --auto-package  # Enable auto-packaging
booth-vcc settings --no-auto-package  # Disable auto-packaging
```

## Auto-Packaging

You can enable automatic packaging of new items as they're downloaded:

```bash
booth-vcc settings --auto-package
```

With this enabled, any new items you download will automatically be packaged and added to your VCC repository.

## Repository Structure

The VCC repository is created at the path specified in your settings (default: `AppData/Local/BoothAssetsManager/Repository` on Windows, `~/Library/Application Support/BoothAssetsManager/Repository` on macOS, or `~/.local/share/BoothAssetsManager/Repository` on Linux).

The repository has the following structure:

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

## Using Packages in Unity

Once you've added your repository to VCC:

1. Open VCC
2. Select your Unity project
3. Go to "Manage Project"
4. Find your repository in the list
5. Browse and install packages from your collection

## Troubleshooting

### Repository Not Found

If VCC can't find your repository:
- Check that the repository path is correct
- Verify that the index.json file exists
- Try regenerating the repository index: `booth-vcc regenerate`

### VCC Protocol Link Doesn't Work

If the VCC protocol link doesn't open:
- Try adding the repository manually in VCC
- Go to Settings > Packages > Add Repository
- Enter the file URL shown in the output of `booth-vcc add-to-vcc`

### Packages Don't Appear in Unity

If packages don't appear in Unity:
- Verify the package structure is correct
- Check that assets are in the Runtime folder
- Ensure the package.json file is valid
- Try regenerating the repository index: `booth-vcc regenerate`

### Invalid Repository Structure

If you get errors about the repository structure:
- Run `booth-vcc validate --fix` to automatically fix common issues
- Check the repository path in settings
- Ensure you have write permissions to the repository directory

## Advanced Usage

### Custom Repository Path

You can set a custom repository path:

```bash
booth-vcc settings --repository-path /path/to/repo
```

### Manual Repository Management

If you need to manually manage the repository:
- The index.json file contains the repository listing
- Each package has its own directory under Packages/
- The package.json file in each package directory contains the package manifest

### Testing VCC Integration

You can test the VCC integration with the included test script:

```bash
python test_vcc.py [--item-id ITEM_ID]
```

This will:
- Enable VCC integration
- Create the repository structure
- Package a test item
- Generate the repository index
- Test the VCC protocol URL
