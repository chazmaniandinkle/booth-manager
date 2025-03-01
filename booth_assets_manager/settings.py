#!/usr/bin/env python3
import os
import json
import platform

class Settings:
    """
    Settings manager for Booth Assets Manager.
    Handles configuration loading, saving, and default values.
    """
    def __init__(self):
        self.config_path = self._get_config_path()
        self.config = self._load_config()
    
    def _get_config_path(self):
        """Get the path to the configuration file based on the platform."""
        if platform.system() == "Windows":
            base_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "BoothAssetsManager")
        elif platform.system() == "Darwin":  # macOS
            base_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "BoothAssetsManager")
        else:  # Linux and others
            base_dir = os.path.join(os.path.expanduser("~"), ".config", "BoothAssetsManager")
        
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, "settings.json")
    
    def _load_config(self):
        """Load configuration from file or create default if it doesn't exist."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"Error loading config from {self.config_path}, using defaults")
                return self._default_config()
        return self._default_config()
    
    def _default_config(self):
        """Create default configuration."""
        if platform.system() == "Windows":
            repo_path = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "BoothAssetsManager", "Repository")
        elif platform.system() == "Darwin":  # macOS
            repo_path = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "BoothAssetsManager", "Repository")
        else:  # Linux and others
            repo_path = os.path.join(os.path.expanduser("~"), ".local", "share", "BoothAssetsManager", "Repository")
        
        return {
            "repository_path": repo_path,
            "vcc_integration_enabled": False,
            "auto_package_new_items": False,
            "repository_name": "Booth Assets Collection",
            "repository_id": "com.boothassetsmanager.repository",
            "repository_author": "booth-assets-manager@example.com"
        }
    
    def save(self):
        """Save current configuration to file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error saving config to {self.config_path}: {e}")
            return False
    
    def get_repository_path(self):
        """Get the repository path from config or default."""
        return self.config.get("repository_path", self._default_config()["repository_path"])
    
    def is_vcc_enabled(self):
        """Check if VCC integration is enabled."""
        return self.config.get("vcc_integration_enabled", False)
    
    def set_vcc_enabled(self, enabled):
        """Enable or disable VCC integration."""
        self.config["vcc_integration_enabled"] = bool(enabled)
        return self.save()
    
    def get_auto_package_new_items(self):
        """Check if new items should be automatically packaged."""
        return self.config.get("auto_package_new_items", False)
    
    def set_auto_package_new_items(self, enabled):
        """Enable or disable automatic packaging of new items."""
        self.config["auto_package_new_items"] = bool(enabled)
        return self.save()
    
    def get_repository_name(self):
        """Get the repository name."""
        return self.config.get("repository_name", self._default_config()["repository_name"])
    
    def set_repository_name(self, name):
        """Set the repository name."""
        self.config["repository_name"] = str(name)
        return self.save()
    
    def get_repository_id(self):
        """Get the repository ID."""
        return self.config.get("repository_id", self._default_config()["repository_id"])
    
    def set_repository_id(self, repo_id):
        """Set the repository ID."""
        self.config["repository_id"] = str(repo_id)
        return self.save()
    
    def get_repository_author(self):
        """Get the repository author."""
        return self.config.get("repository_author", self._default_config()["repository_author"])
    
    def set_repository_author(self, author):
        """Set the repository author."""
        self.config["repository_author"] = str(author)
        return self.save()
    
    def ensure_repository_structure(self):
        """Ensure the repository directory structure exists."""
        repo_path = self.get_repository_path()
        packages_path = os.path.join(repo_path, "Packages")
        
        try:
            os.makedirs(repo_path, exist_ok=True)
            os.makedirs(packages_path, exist_ok=True)
            return True
        except OSError as e:
            print(f"Error creating repository structure: {e}")
            return False

# Initialize settings
settings = Settings()
