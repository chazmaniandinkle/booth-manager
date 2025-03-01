#!/usr/bin/env python3
import sys
import os
import asyncio
import threading
import time
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QProgressBar, QFileDialog, QComboBox, QCheckBox,
    QGroupBox, QFormLayout, QTextEdit, QScrollArea, QSplitter, QFrame,
    QHeaderView, QDialog, QListWidget, QListWidgetItem, QStackedWidget,
    QToolBar, QStatusBar, QMenu, QMenuBar
)
from PyQt6.QtGui import QPixmap, QIcon, QAction, QColor, QFont
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, pyqtSlot, QSize, QTimer, 
    QUrl, QDir, QCoreApplication
)

from .database import Database
from .settings import settings
from .browser_auth import BrowserAuth, interactive_login, check_auth_status
from .booth_downloader import get_purchased_items, get_download_links, download_all_files
from .organizer import parse_input_file, ensure_item_folder, add_items, extract_item_id
from .vcc_integration import (
    package_item, generate_repository_index, open_vcc_integration, 
    validate_repository, test_vcc_integration
)

# Worker thread for background tasks
class Worker(QThread):
    finished = pyqtSignal(object)
    progress = pyqtSignal(int, str)
    error = pyqtSignal(str)
    
    def __init__(self, task, *args, **kwargs):
        super().__init__()
        self.task = task
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.task(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# Main application window
class BoothAssetsManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.auth = BrowserAuth()
        self.workers = []  # Keep references to worker threads
        
        self.init_ui()
        self.load_items()
        self.check_auth_status()
        
    def init_ui(self):
        # Setup main window
        self.setWindowTitle("Booth Assets Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Setup menubar
        self.create_menubar()
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        # Create main tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Create tabs
        self.dashboard_tab = self.create_dashboard_tab()
        self.items_tab = self.create_items_tab()
        self.downloads_tab = self.create_downloads_tab()
        self.vcc_tab = self.create_vcc_tab()
        self.settings_tab = self.create_settings_tab()
        
        # Add tabs to widget
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.items_tab, "Items")
        self.tabs.addTab(self.downloads_tab, "Downloads")
        self.tabs.addTab(self.vcc_tab, "VCC Integration")
        self.tabs.addTab(self.settings_tab, "Settings")
        
        # Set up application icon
        # self.setWindowIcon(QIcon('assets/icon.png'))
        
        # Connect tab changed signal
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Show window
        self.show()
    
    def create_menubar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        import_action = QAction("Import Items...", self)
        import_action.triggered.connect(self.show_import_dialog)
        file_menu.addAction(import_action)
        
        export_action = QAction("Export Data...", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(lambda: self.tabs.setCurrentIndex(4))
        edit_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    def create_dashboard_tab(self):
        # Create widget and layout
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Welcome header
        header = QLabel("Booth Assets Manager")
        header.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)
        
        welcome_text = QLabel("Welcome to Booth Assets Manager. This tool helps you organize and manage your Booth marketplace assets.")
        layout.addWidget(welcome_text)
        
        # Stats section
        stats_group = QGroupBox("Overview")
        stats_layout = QFormLayout()
        stats_group.setLayout(stats_layout)
        
        self.total_items_label = QLabel("0")
        self.purchased_items_label = QLabel("0")
        self.downloaded_files_label = QLabel("0")
        self.packaged_items_label = QLabel("0")
        
        stats_layout.addRow("Total Items:", self.total_items_label)
        stats_layout.addRow("Purchased Items:", self.purchased_items_label)
        stats_layout.addRow("Downloaded Files:", self.downloaded_files_label)
        stats_layout.addRow("VCC Packaged Items:", self.packaged_items_label)
        
        layout.addWidget(stats_group)
        
        # Quick actions section
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout()
        actions_group.setLayout(actions_layout)
        
        # Import items button
        import_btn = QPushButton("Import Items")
        import_btn.clicked.connect(self.show_import_dialog)
        actions_layout.addWidget(import_btn)
        
        # Login to Booth button
        self.login_btn = QPushButton("Login to Booth")
        self.login_btn.clicked.connect(self.login_to_booth)
        actions_layout.addWidget(self.login_btn)
        
        # Download all purchased items button
        self.download_all_btn = QPushButton("Download All Purchased Items")
        self.download_all_btn.clicked.connect(self.download_all_purchased)
        self.download_all_btn.setEnabled(False)  # Disabled until authenticated
        actions_layout.addWidget(self.download_all_btn)
        
        # Enable VCC integration button
        self.vcc_toggle_btn = QPushButton("Enable VCC Integration")
        self.vcc_toggle_btn.clicked.connect(self.toggle_vcc)
        actions_layout.addWidget(self.vcc_toggle_btn)
        
        layout.addWidget(actions_group)
        
        # Recent activity section
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout()
        activity_group.setLayout(activity_layout)
        
        self.activity_list = QListWidget()
        activity_layout.addWidget(self.activity_list)
        
        layout.addWidget(activity_group)
        
        # Update dashboard data
        self.update_dashboard()
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return tab
    
    def create_items_tab(self):
        # Create widget and layout
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Top controls
        controls_layout = QHBoxLayout()
        
        # Search
        search_label = QLabel("Search:")
        controls_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title or ID...")
        self.search_input.textChanged.connect(self.filter_items)
        controls_layout.addWidget(self.search_input)
        
        # Filter dropdown
        filter_label = QLabel("Filter:")
        controls_layout.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Items", "Purchased Only", "VCC Packaged"])
        self.filter_combo.currentIndexChanged.connect(self.filter_items)
        controls_layout.addWidget(self.filter_combo)
        
        # Import button
        import_btn = QPushButton("Import Items")
        import_btn.clicked.connect(self.show_import_dialog)
        controls_layout.addWidget(import_btn)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_items)
        controls_layout.addWidget(refresh_btn)
        
        layout.addLayout(controls_layout)
        
        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(["ID", "Title", "Purchased", "Packaged", "Files", "Actions"])
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.items_table.cellDoubleClicked.connect(self.show_item_details)
        
        layout.addWidget(self.items_table)
        
        # Status message
        self.items_status = QLabel("")
        layout.addWidget(self.items_status)
        
        return tab
    
    def create_downloads_tab(self):
        # Create widget and layout
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Authentication section
        auth_group = QGroupBox("Authentication")
        auth_layout = QVBoxLayout()
        auth_group.setLayout(auth_layout)
        
        # Authentication status
        auth_status_layout = QHBoxLayout()
        auth_status_label = QLabel("Status:")
        auth_status_layout.addWidget(auth_status_label)
        
        self.auth_status = QLabel("Not authenticated")
        auth_status_layout.addWidget(self.auth_status)
        
        self.auth_login_btn = QPushButton("Login to Booth")
        self.auth_login_btn.clicked.connect(self.login_to_booth)
        auth_status_layout.addWidget(self.auth_login_btn)
        
        self.auth_logout_btn = QPushButton("Logout")
        self.auth_logout_btn.clicked.connect(self.logout_from_booth)
        self.auth_logout_btn.setEnabled(False)
        auth_status_layout.addWidget(self.auth_logout_btn)
        
        auth_layout.addLayout(auth_status_layout)
        layout.addWidget(auth_group)
        
        # Purchases section
        purchases_group = QGroupBox("Purchased Items")
        purchases_layout = QVBoxLayout()
        purchases_group.setLayout(purchases_layout)
        
        # Controls
        purchases_controls = QHBoxLayout()
        
        self.fetch_purchases_btn = QPushButton("Fetch Purchases")
        self.fetch_purchases_btn.clicked.connect(self.fetch_purchases)
        self.fetch_purchases_btn.setEnabled(False)
        purchases_controls.addWidget(self.fetch_purchases_btn)
        
        self.update_db_checkbox = QCheckBox("Update Database")
        self.update_db_checkbox.setChecked(True)
        purchases_controls.addWidget(self.update_db_checkbox)
        
        self.download_selected_btn = QPushButton("Download Selected")
        self.download_selected_btn.clicked.connect(self.download_selected)
        self.download_selected_btn.setEnabled(False)
        purchases_controls.addWidget(self.download_selected_btn)
        
        self.download_all_purchases_btn = QPushButton("Download All")
        self.download_all_purchases_btn.clicked.connect(self.download_all_purchased)
        self.download_all_purchases_btn.setEnabled(False)
        purchases_controls.addWidget(self.download_all_purchases_btn)
        
        purchases_layout.addLayout(purchases_controls)
        
        # Purchases table
        self.purchases_table = QTableWidget()
        self.purchases_table.setColumnCount(5)
        self.purchases_table.setHorizontalHeaderLabels(["ID", "Title", "Purchase Date", "Price", "Status"])
        self.purchases_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.purchases_table.verticalHeader().setVisible(False)
        self.purchases_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        purchases_layout.addWidget(self.purchases_table)
        layout.addWidget(purchases_group)
        
        # Downloads section
        downloads_group = QGroupBox("Downloads")
        downloads_layout = QVBoxLayout()
        downloads_group.setLayout(downloads_layout)
        
        self.downloads_table = QTableWidget()
        self.downloads_table.setColumnCount(5)
        self.downloads_table.setHorizontalHeaderLabels(["Item", "Filename", "Size", "Date", "Status"])
        self.downloads_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.downloads_table.verticalHeader().setVisible(False)
        
        downloads_layout.addWidget(self.downloads_table)
        
        # Progress bar for current download
        progress_layout = QHBoxLayout()
        progress_label = QLabel("Progress:")
        progress_layout.addWidget(progress_label)
        
        self.download_progress = QProgressBar()
        self.download_progress.setRange(0, 100)
        self.download_progress.setValue(0)
        progress_layout.addWidget(self.download_progress)
        
        downloads_layout.addLayout(progress_layout)
        layout.addWidget(downloads_group)
        
        return tab
    
    def create_vcc_tab(self):
        # Create widget and layout
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # VCC Status section
        status_group = QGroupBox("VCC Integration Status")
        status_layout = QFormLayout()
        status_group.setLayout(status_layout)
        
        self.vcc_enabled_label = QLabel("Disabled")
        self.repo_path_label = QLabel("")
        self.repo_exists_label = QLabel("No")
        self.index_valid_label = QLabel("No")
        self.packages_found_label = QLabel("0")
        self.overall_status_label = QLabel("Not configured")
        
        status_layout.addRow("VCC Integration:", self.vcc_enabled_label)
        status_layout.addRow("Repository Path:", self.repo_path_label)
        status_layout.addRow("Repository Exists:", self.repo_exists_label)
        status_layout.addRow("Index Valid:", self.index_valid_label)
        status_layout.addRow("Packages Found:", self.packages_found_label)
        status_layout.addRow("Overall Status:", self.overall_status_label)
        
        # Control buttons
        status_buttons_layout = QHBoxLayout()
        
        self.vcc_enable_btn = QPushButton("Enable VCC Integration")
        self.vcc_enable_btn.clicked.connect(self.enable_vcc)
        status_buttons_layout.addWidget(self.vcc_enable_btn)
        
        self.vcc_disable_btn = QPushButton("Disable VCC Integration")
        self.vcc_disable_btn.clicked.connect(self.disable_vcc)
        self.vcc_disable_btn.setEnabled(False)
        status_buttons_layout.addWidget(self.vcc_disable_btn)
        
        self.check_vcc_btn = QPushButton("Check Status")
        self.check_vcc_btn.clicked.connect(self.check_vcc_status)
        status_buttons_layout.addWidget(self.check_vcc_btn)
        
        status_layout.addRow("", status_buttons_layout)
        
        layout.addWidget(status_group)
        
        # VCC Actions section
        actions_group = QGroupBox("VCC Actions")
        actions_layout = QVBoxLayout()
        actions_group.setLayout(actions_layout)
        
        actions_buttons = QHBoxLayout()
        
        self.add_repo_btn = QPushButton("Add Repository to VCC")
        self.add_repo_btn.clicked.connect(self.add_repo_to_vcc)
        self.add_repo_btn.setEnabled(False)
        actions_buttons.addWidget(self.add_repo_btn)
        
        self.regen_index_btn = QPushButton("Regenerate Index")
        self.regen_index_btn.clicked.connect(self.regenerate_index)
        self.regen_index_btn.setEnabled(False)
        actions_buttons.addWidget(self.regen_index_btn)
        
        self.package_all_btn = QPushButton("Package All Items")
        self.package_all_btn.clicked.connect(self.package_all_items)
        self.package_all_btn.setEnabled(False)
        actions_buttons.addWidget(self.package_all_btn)
        
        actions_layout.addLayout(actions_buttons)
        
        # Package table
        self.packages_table = QTableWidget()
        self.packages_table.setColumnCount(4)
        self.packages_table.setHorizontalHeaderLabels(["ID", "Title", "Package ID", "Actions"])
        self.packages_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.packages_table.verticalHeader().setVisible(False)
        
        actions_layout.addWidget(self.packages_table)
        
        layout.addWidget(actions_group)
        
        # Auto-package setting
        auto_package_layout = QHBoxLayout()
        self.auto_package_checkbox = QCheckBox("Automatically package new items")
        self.auto_package_checkbox.setEnabled(False)
        self.auto_package_checkbox.stateChanged.connect(self.toggle_auto_package)
        auto_package_layout.addWidget(self.auto_package_checkbox)
        
        layout.addLayout(auto_package_layout)
        
        # Initialize VCC status
        self.check_vcc_status()
        
        return tab
    
    def create_settings_tab(self):
        # Create widget and layout
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Paths section
        paths_group = QGroupBox("Paths")
        paths_layout = QFormLayout()
        paths_group.setLayout(paths_layout)
        
        # Base items directory
        base_dir_layout = QHBoxLayout()
        self.base_dir_input = QLineEdit()
        self.base_dir_input.setText("BoothItems")
        base_dir_layout.addWidget(self.base_dir_input)
        
        browse_base_dir_btn = QPushButton("Browse...")
        browse_base_dir_btn.clicked.connect(lambda: self.browse_directory(self.base_dir_input))
        base_dir_layout.addWidget(browse_base_dir_btn)
        
        paths_layout.addRow("Items Directory:", base_dir_layout)
        
        # Downloads directory
        downloads_dir_layout = QHBoxLayout()
        self.downloads_dir_input = QLineEdit()
        self.downloads_dir_input.setText(settings.config.get("download_directory", "BoothDownloads"))
        downloads_dir_layout.addWidget(self.downloads_dir_input)
        
        browse_downloads_dir_btn = QPushButton("Browse...")
        browse_downloads_dir_btn.clicked.connect(lambda: self.browse_directory(self.downloads_dir_input))
        downloads_dir_layout.addWidget(browse_downloads_dir_btn)
        
        paths_layout.addRow("Downloads Directory:", downloads_dir_layout)
        
        # VCC Repository directory
        vcc_repo_dir_layout = QHBoxLayout()
        self.vcc_repo_dir_input = QLineEdit()
        self.vcc_repo_dir_input.setText(settings.get_repository_path())
        vcc_repo_dir_layout.addWidget(self.vcc_repo_dir_input)
        
        browse_vcc_repo_dir_btn = QPushButton("Browse...")
        browse_vcc_repo_dir_btn.clicked.connect(lambda: self.browse_directory(self.vcc_repo_dir_input))
        vcc_repo_dir_layout.addWidget(browse_vcc_repo_dir_btn)
        
        paths_layout.addRow("VCC Repository:", vcc_repo_dir_layout)
        
        layout.addWidget(paths_group)
        
        # VCC Settings section
        vcc_settings_group = QGroupBox("VCC Settings")
        vcc_settings_layout = QFormLayout()
        vcc_settings_group.setLayout(vcc_settings_layout)
        
        self.repo_name_input = QLineEdit()
        self.repo_name_input.setText(settings.get_repository_name())
        vcc_settings_layout.addRow("Repository Name:", self.repo_name_input)
        
        self.repo_id_input = QLineEdit()
        self.repo_id_input.setText(settings.get_repository_id())
        vcc_settings_layout.addRow("Repository ID:", self.repo_id_input)
        
        self.repo_author_input = QLineEdit()
        self.repo_author_input.setText(settings.get_repository_author())
        vcc_settings_layout.addRow("Repository Author:", self.repo_author_input)
        
        layout.addWidget(vcc_settings_group)
        
        # Download Settings section
        download_settings_group = QGroupBox("Download Settings")
        download_settings_layout = QFormLayout()
        download_settings_group.setLayout(download_settings_layout)
        
        self.concurrent_downloads_input = QComboBox()
        self.concurrent_downloads_input.addItems(["1", "2", "3", "4", "5"])
        self.concurrent_downloads_input.setCurrentText("3")
        download_settings_layout.addRow("Concurrent Downloads:", self.concurrent_downloads_input)
        
        layout.addWidget(download_settings_group)
        
        # Save Settings button
        save_settings_btn = QPushButton("Save Settings")
        save_settings_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_btn)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return tab
    
    # Dashboard functionality
    def update_dashboard(self):
        """Update the dashboard with current stats and activity"""
        # Update stats
        all_items = self.db.get_all_items()
        purchased_items = self.db.get_purchased_items()
        packaged_items = self.db.get_packaged_items()
        
        # Count downloads
        downloaded_files = 0
        for item in all_items:
            downloaded_files += len(item.get('downloads', []))
        
        self.total_items_label.setText(str(len(all_items)))
        self.purchased_items_label.setText(str(len(purchased_items)))
        self.downloaded_files_label.setText(str(downloaded_files))
        self.packaged_items_label.setText(str(len(packaged_items)))
        
        # Update VCC button text
        if settings.is_vcc_enabled():
            self.vcc_toggle_btn.setText("Disable VCC Integration")
        else:
            self.vcc_toggle_btn.setText("Enable VCC Integration")
        
        # Clear and update activity list
        self.activity_list.clear()
        
        # Add recent activities - this would ideally come from a log or history
        # For now, we'll add some placeholder items
        activities = [
            "Application started",
            f"Loaded {len(all_items)} items from database"
        ]
        
        if self.auth.is_authenticated():
            activities.append("Authenticated with Booth")
        
        # Most recent activity should be at the top
        for activity in reversed(activities):
            item = QListWidgetItem(f"{datetime.now().strftime('%H:%M:%S')} - {activity}")
            self.activity_list.addItem(item)
    
    # Items Tab functionality
    def load_items(self):
        """Load items from the database into the items table"""
        self.statusBar.showMessage("Loading items...")
        
        # Use a worker thread to load items
        worker = Worker(self.db.get_all_items)
        worker.finished.connect(self.display_items)
        worker.error.connect(self.show_error)
        worker.start()
        
        # Store worker reference
        self.workers.append(worker)
    
    def display_items(self, items):
        """Display items in the items table"""
        self.all_items = items  # Store for filtering
        
        # Clear the table
        self.items_table.setRowCount(0)
        
        if not items:
            self.items_status.setText("No items found in database.")
            self.statusBar.showMessage("No items found.")
            return
        
        # Populate the table
        for row, item in enumerate(items):
            self.items_table.insertRow(row)
            
            # ID
            id_item = QTableWidgetItem(item['item_id'])
            id_item.setData(Qt.ItemDataRole.UserRole, item)  # Store the full item data
            self.items_table.setItem(row, 0, id_item)
            
            # Title
            title_item = QTableWidgetItem(item['title'])
            self.items_table.setItem(row, 1, title_item)
            
            # Purchased
            purchased = "Yes" if item.get('is_purchased') else "No"
            purchased_item = QTableWidgetItem(purchased)
            if item.get('is_purchased'):
                purchased_item.setBackground(QColor(200, 255, 200))  # Light green
            self.items_table.setItem(row, 2, purchased_item)
            
            # Packaged
            packaged = "Yes" if item.get('is_packaged') else "No"
            packaged_item = QTableWidgetItem(packaged)
            if item.get('is_packaged'):
                packaged_item.setBackground(QColor(200, 200, 255))  # Light blue
            self.items_table.setItem(row, 3, packaged_item)
            
            # Files count
            files_count = len(item.get('downloads', []))
            files_item = QTableWidgetItem(str(files_count))
            self.items_table.setItem(row, 4, files_item)
            
            # Actions - would usually be buttons
            actions_item = QTableWidgetItem("View Details")
            self.items_table.setItem(row, 5, actions_item)
        
        self.items_status.setText(f"Showing {len(items)} items.")
        self.statusBar.showMessage(f"Loaded {len(items)} items.")
        
        # Update dashboard
        self.update_dashboard()
    
    def filter_items(self):
        """Filter items based on search text and filter selection"""
        search_text = self.search_input.text().lower()
        filter_option = self.filter_combo.currentText()
        
        filtered_items = []
        for item in self.all_items:
            # Apply text search
            if search_text and search_text not in item['title'].lower() and search_text not in item['item_id']:
                continue
            
            # Apply filter
            if filter_option == "Purchased Only" and not item.get('is_purchased'):
                continue
            if filter_option == "VCC Packaged" and not item.get('is_packaged'):
                continue
            
            filtered_items.append(item)
        
        # Update table
        self.display_items(filtered_items)
    
    def show_item_details(self, row, column):
        """Show details dialog for the selected item"""
        item_data = self.items_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        # Create details dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Item Details: {item_data['title']}")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        # Item details
        details_group = QGroupBox("Item Details")
        details_layout = QFormLayout()
        details_group.setLayout(details_layout)
        
        details_layout.addRow("ID:", QLabel(item_data['item_id']))
        details_layout.addRow("Title:", QLabel(item_data['title']))
        details_layout.addRow("URL:", QLabel(f"<a href='{item_data['url']}'>{item_data['url']}</a>"))
        
        if item_data.get('is_purchased'):
            purchase_info = QLabel(f"Purchased on {item_data.get('purchase_date', 'Unknown date')}")
            purchase_info.setStyleSheet("color: green;")
            details_layout.addRow("Purchase:", purchase_info)
        
        if item_data.get('is_packaged'):
            package_info = QLabel(f"Packaged as {item_data.get('package_id', 'Unknown')}")
            package_info.setStyleSheet("color: blue;")
            details_layout.addRow("VCC Package:", package_info)
        
        folder_path = QLabel(item_data.get('folder', 'Unknown'))
        folder_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        details_layout.addRow("Folder:", folder_path)
        
        layout.addWidget(details_group)
        
        # Description
        if item_data.get('description'):
            desc_group = QGroupBox("Description")
            desc_layout = QVBoxLayout()
            desc_group.setLayout(desc_layout)
            
            desc_text = QTextEdit()
            desc_text.setPlainText(item_data.get('description', ''))
            desc_text.setReadOnly(True)
            desc_layout.addWidget(desc_text)
            
            layout.addWidget(desc_group)
        
        # Images
        if item_data.get('local_images'):
            images_group = QGroupBox("Preview Images")
            images_layout = QHBoxLayout()
            images_group.setLayout(images_layout)
            
            for img_path in item_data.get('local_images', []):
                if os.path.exists(img_path):
                    img_label = QLabel()
                    pixmap = QPixmap(img_path)
                    pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
                    img_label.setPixmap(pixmap)
                    images_layout.addWidget(img_label)
            
            layout.addWidget(images_group)
        
        # Downloads
        if item_data.get('downloads'):
            downloads_group = QGroupBox("Downloaded Files")
            downloads_layout = QVBoxLayout()
            downloads_group.setLayout(downloads_layout)
            
            downloads_table = QTableWidget()
            downloads_table.setColumnCount(3)
            downloads_table.setHorizontalHeaderLabels(["Filename", "Date", "Status"])
            downloads_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            downloads_table.verticalHeader().setVisible(False)
            
            for row, download in enumerate(item_data.get('downloads', [])):
                downloads_table.insertRow(row)
                downloads_table.setItem(row, 0, QTableWidgetItem(download.get('filename', 'Unknown')))
                downloads_table.setItem(row, 1, QTableWidgetItem(download.get('download_date', 'Unknown')))
                downloads_table.setItem(row, 2, QTableWidgetItem(download.get('status', 'Unknown')))
            
            downloads_layout.addWidget(downloads_table)
            layout.addWidget(downloads_group)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        if not item_data.get('is_packaged') and settings.is_vcc_enabled():
            package_btn = QPushButton("Package for VCC")
            package_btn.clicked.connect(lambda: self.package_item(item_data))
            buttons_layout.addWidget(package_btn)
        
        if item_data.get('is_purchased') and not item_data.get('downloads'):
            download_btn = QPushButton("Download Files")
            download_btn.clicked.connect(lambda: self.download_item(item_data))
            buttons_layout.addWidget(download_btn)
        
        open_folder_btn = QPushButton("Open Folder")
        open_folder_btn.clicked.connect(lambda: self.open_folder(item_data.get('folder')))
        buttons_layout.addWidget(open_folder_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
        # Show dialog
        dialog.exec()
    
    def show_import_dialog(self):
        """Show dialog for importing items"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Import Items")
        dialog.setMinimumWidth(600)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        # Import by URL(s)
        url_group = QGroupBox("Import by URL")
        url_layout = QVBoxLayout()
        url_group.setLayout(url_layout)
        
        url_desc = QLabel("Enter Booth item URLs or IDs, one per line:")
        url_layout.addWidget(url_desc)
        
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("https://booth.pm/items/123456\nhttps://booth.pm/items/789012\n123456\n789012")
        url_layout.addWidget(self.url_input)
        
        layout.addWidget(url_group)
        
        # Import from file
        file_group = QGroupBox("Import from File")
        file_layout = QHBoxLayout()
        file_group.setLayout(file_layout)
        
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select a CSV, JSON, or text file...")
        file_layout.addWidget(self.file_input)
        
        browse_file_btn = QPushButton("Browse...")
        browse_file_btn.clicked.connect(self.browse_import_file)
        file_layout.addWidget(browse_file_btn)
        
        layout.addWidget(file_group)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.force_update_checkbox = QCheckBox("Force update (re-download metadata and images)")
        options_layout.addWidget(self.force_update_checkbox)
        
        layout.addLayout(options_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        import_btn = QPushButton("Import")
        import_btn.clicked.connect(lambda: self.import_items(dialog))
        buttons_layout.addWidget(import_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # Show dialog
        dialog.exec()
    
    def browse_import_file(self):
        """Browse for an import file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Import File", "", 
            "All Supported Files (*.csv *.json *.txt);;CSV Files (*.csv);;JSON Files (*.json);;Text Files (*.txt)"
        )
        if file_path:
            self.file_input.setText(file_path)
    
    def import_items(self, dialog):
        """Import items from the import dialog"""
        # Get import data
        urls = self.url_input.toPlainText().strip()
        file_path = self.file_input.text().strip()
        force_update = self.force_update_checkbox.isChecked()
        
        if not urls and not file_path:
            QMessageBox.warning(self, "No Input", "Please enter URLs or select a file to import.")
            return
        
        # Process URLs directly if provided
        if urls:
            # Write URLs to a temporary file
            temp_file = os.path.join(os.path.dirname(settings.config_path), "temp_import.txt")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(urls)
            
            file_path = temp_file
        
        # Close the dialog
        dialog.accept()
        
        # Show progress message
        self.statusBar.showMessage(f"Importing items from {file_path}...")
        
        # Use a worker thread to import items
        worker = Worker(add_items, file_path, force_update)
        worker.finished.connect(lambda: self.import_finished(file_path))
        worker.error.connect(self.show_error)
        worker.start()
        
        # Store worker reference
        self.workers.append(worker)
    
    def import_finished(self, file_path):
        """Handle import completion"""
        self.statusBar.showMessage("Import completed.")
        
        # Reload items
        self.load_items()
        
        # Clean up temporary file if used
        if os.path.basename(file_path) == "temp_import.txt":
            try:
                os.remove(file_path)
            except:
                pass
    
    # Downloads Tab functionality
    def check_auth_status(self):
        """Check authentication status and update UI"""
        worker = Worker(self.auth.is_authenticated)
        worker.finished.connect(self.update_auth_status)
        worker.error.connect(self.show_error)
        worker.start()
        
        # Store worker reference
        self.workers.append(worker)
    
    def update_auth_status(self, is_authenticated):
        """Update the UI based on authentication status"""
        if is_authenticated:
            self.auth_status.setText("Authenticated")
            self.auth_status.setStyleSheet("color: green; font-weight: bold;")
            self.auth_login_btn.setEnabled(False)
            self.auth_logout_btn.setEnabled(True)
            self.fetch_purchases_btn.setEnabled(True)
            self.download_all_btn.setEnabled(True)
            self.download_all_purchases_btn.setEnabled(True)
        else:
            self.auth_status.setText("Not authenticated")
            self.auth_status.setStyleSheet("color: red;")
            self.auth_login_btn.setEnabled(True)
            self.auth_logout_btn.setEnabled(False)
            self.fetch_purchases_btn.setEnabled(False)
            self.download_all_btn.setEnabled(False)
            self.download_all_purchases_btn.setEnabled(False)
            self.download_selected_btn.setEnabled(False)
    
    def login_to_booth(self):
        """Initiate Booth login process"""
        # Show message
        self.statusBar.showMessage("Opening browser for Booth login...")
        
        # Start login process in a worker thread
        worker = Worker(interactive_login)
        worker.finished.connect(self.login_finished)
        worker.error.connect(self.show_error)
        worker.start()
        
        # Store worker reference
        self.workers.append(worker)
    
    def login_finished(self, success):
        """Handle login completion"""
        if success:
            self.statusBar.showMessage("Login successful.")
            self.check_auth_status()
            
            # Add activity to dashboard
            self.activity_list.insertItem(0, QListWidgetItem(f"{datetime.now().strftime('%H:%M:%S')} - Logged in to Booth"))
        else:
            self.statusBar.showMessage("Login failed or was cancelled.")
            QMessageBox.warning(self, "Login Failed", "Login to Booth failed or was cancelled.")
    
    def logout_from_booth(self):
        """Log out from Booth"""
        # Clear cookie file
        cookies_file = settings.config.get("auth_cookies_file")
        if cookies_file and os.path.exists(cookies_file):
            try:
                os.remove(cookies_file)
            except Exception as e:
                self.show_error(f"Error removing cookies file: {e}")
                return
        
        # Clear auth settings
        settings.config["auth_cookies_file"] = None
        settings.config["last_login"] = None
        settings.save()
        
        # Update UI
        self.check_auth_status()
        self.statusBar.showMessage("Logged out from Booth.")
        
        # Add activity to dashboard
        self.activity_list.insertItem(0, QListWidgetItem(f"{datetime.now().strftime('%H:%M:%S')} - Logged out from Booth"))
    
    def fetch_purchases(self):
        """Fetch purchases from Booth"""
        # Show message
        self.statusBar.showMessage("Fetching purchases from Booth...")
        
        # Start fetch process in a worker thread
        worker = Worker(get_purchased_items)
        worker.finished.connect(self.display_purchases)
        worker.error.connect(self.show_error)
        worker.start()
        
        # Store worker reference
        self.workers.append(worker)
    
    def display_purchases(self, purchases):
        """Display purchases in the purchases table"""
        # Store purchases for use in downloads
        self.purchases = purchases
        
        # Clear the table
        self.purchases_table.setRowCount(0)
        
        if not purchases:
            self.statusBar.showMessage("No purchases found.")
            return
        
        # Populate the table
        for row, item in enumerate(purchases):
            self.purchases_table.insertRow(row)
            
            # ID
            id_item = QTableWidgetItem(item['item_id'])
            id_item.setData(Qt.ItemDataRole.UserRole, item)  # Store the full item data
            self.purchases_table.setItem(row, 0, id_item)
            
            # Title
            title_item = QTableWidgetItem(item['title'])
            self.purchases_table.setItem(row, 1, title_item)
            
            # Purchase Date
            purchase_date = QTableWidgetItem(item.get('purchase_date', 'Unknown'))
            self.purchases_table.setItem(row, 2, purchase_date)
            
            # Price
            price = QTableWidgetItem(item.get('price', 'Unknown'))
            self.purchases_table.setItem(row, 3, price)
            
            # Status - check if already downloaded
            existing_item = self.db.get_item(item['item_id'])
            status_text = "Not downloaded"
            if existing_item and existing_item.get('downloads'):
                status_text = f"Downloaded ({len(existing_item['downloads'])} files)"
            
            status = QTableWidgetItem(status_text)
            self.purchases_table.setItem(row, 4, status)
        
        self.statusBar.showMessage(f"Found {len(purchases)} purchased items.")
        self.download_selected_btn.setEnabled(True)
        
        # Update database if needed
        if self.update_db_checkbox.isChecked():
            self.update_db_with_purchases(purchases)
    
    def update_db_with_purchases(self, purchases):
        """Update database with purchase information"""
        for item in purchases:
            # Check if item exists in database
            existing_item = self.db.get_item(item['item_id'])
            
            if existing_item:
                # Update existing item
                self.db.update_item(
                    item['item_id'],
                    is_purchased=True,
                    purchase_date=item.get('purchase_date'),
                    purchase_price=item.get('price')
                )
            else:
                # Add new item
                self.db.add_item(
                    item_id=item['item_id'],
                    title=item['title'],
                    url=item['url'],
                    is_purchased=True,
                    purchase_date=item.get('purchase_date'),
                    purchase_price=item.get('price')
                )
        
        self.statusBar.showMessage(f"Updated database with {len(purchases)} purchased items.")
        
        # Add activity to dashboard
        self.activity_list.insertItem(0, QListWidgetItem(f"{datetime.now().strftime('%H:%M:%S')} - Updated database with {len(purchases)} purchases"))
        
        # Refresh items list
        self.load_items()
    
    def download_selected(self):
        """Download selected items from the purchases table"""
        selected_rows = self.purchases_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select one or more items to download.")
            return
        
        # Get selected items
        selected_items = []
        for row in selected_rows:
            item_data = self.purchases_table.item(row.row(), 0).data(Qt.ItemDataRole.UserRole)
            selected_items.append(item_data)
        
        # Confirm download
        reply = QMessageBox.question(
            self, "Download Files", 
            f"Download files for {len(selected_items)} selected items?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Disable buttons during download
        self.download_selected_btn.setEnabled(False)
        self.download_all_purchases_btn.setEnabled(False)
        
        # Start download for each item
        for item in selected_items:
            self.download_item(item)
    
    def download_all_purchased(self):
        """Download all purchased items"""
        # Fetch purchases first if not already done
        if not hasattr(self, 'purchases') or not self.purchases:
            self.fetch_purchases()
            return
        
        # Confirm download
        reply = QMessageBox.question(
            self, "Download All Files", 
            f"Download files for all {len(self.purchases)} purchased items?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Disable buttons during download
        self.download_all_btn.setEnabled(False)
        self.download_all_purchases_btn.setEnabled(False)
        
        # Get concurrent download limit
        try:
            concurrent_limit = int(self.concurrent_downloads_input.currentText())
        except:
            concurrent_limit = 3
        
        # Show message
        self.statusBar.showMessage(f"Downloading files for {len(self.purchases)} items...")
        
        # Start download for all items
        for item in self.purchases:
            self.download_item(item, concurrent_limit)
    
    def download_item(self, item, concurrent_limit=3):
        """Download files for an item"""
        # Show message
        self.statusBar.showMessage(f"Downloading files for {item['title']}...")
        
        # Start download process in a worker thread
        worker = Worker(
            download_all_files, 
            item['item_id'], 
            item['title'],
            concurrent_limit
        )
        worker.finished.connect(lambda results: self.download_finished(results, item))
        worker.error.connect(self.show_error)
        worker.start()
        
        # Store worker reference
        self.workers.append(worker)
    
    def download_finished(self, results, item):
        """Handle download completion"""
        if not results:
            self.statusBar.showMessage(f"No files downloaded for {item['title']}.")
            return
        
        successful = [r for r in results if r['success']]
        
        # Update status message
        self.statusBar.showMessage(
            f"Downloaded {len(successful)}/{len(results)} files for {item['title']}."
        )
        
        # Update database
        for result in results:
            if result['success'] and result['path']:
                # Add download to database
                self.db.add_or_update_download(
                    item_id=item['item_id'],
                    filename=result['filename'],
                    local_path=result['path'],
                    download_date=datetime.now().isoformat()
                )
        
        # Add activity to dashboard
        self.activity_list.insertItem(0, QListWidgetItem(
            f"{datetime.now().strftime('%H:%M:%S')} - Downloaded {len(successful)} files for {item['title']}"
        ))
        
        # Refresh items list
        self.load_items()
        
        # Re-enable download buttons
        self.download_selected_btn.setEnabled(True)
        self.download_all_purchases_btn.setEnabled(True)
        self.download_all_btn.setEnabled(True)
        
        # Update downloads table
        self.update_downloads_table()
    
    def update_downloads_table(self):
        """Update the downloads table with all downloads"""
        # Clear the table
        self.downloads_table.setRowCount(0)
        
        # Get all items with downloads
        items = self.db.get_all_items()
        downloads = []
        
        for item in items:
            for download in item.get('downloads', []):
                downloads.append({
                    'item_id': item['item_id'],
                    'item_title': item['title'],
                    'filename': download.get('filename', 'Unknown'),
                    'local_path': download.get('local_path', ''),
                    'date': download.get('download_date', 'Unknown'),
                    'status': download.get('status', 'Unknown')
                })
        
        # Sort by date (newest first)
        downloads.sort(key=lambda x: x['date'], reverse=True)
        
        # Populate the table
        for row, download in enumerate(downloads):
            self.downloads_table.insertRow(row)
            
            # Item
            item_text = f"{download['item_title']} ({download['item_id']})"
            self.downloads_table.setItem(row, 0, QTableWidgetItem(item_text))
            
            # Filename
            self.downloads_table.setItem(row, 1, QTableWidgetItem(download['filename']))
            
            # Size - would need to get from file
            size = "Unknown"
            if download['local_path'] and os.path.exists(download['local_path']):
                try:
                    size_bytes = os.path.getsize(download['local_path'])
                    if size_bytes < 1024:
                        size = f"{size_bytes} B"
                    elif size_bytes < 1024 * 1024:
                        size = f"{size_bytes/1024:.1f} KB"
                    else:
                        size = f"{size_bytes/(1024*1024):.1f} MB"
                except:
                    pass
            
            self.downloads_table.setItem(row, 2, QTableWidgetItem(size))
            
            # Date
            self.downloads_table.setItem(row, 3, QTableWidgetItem(download['date']))
            
            # Status
            self.downloads_table.setItem(row, 4, QTableWidgetItem(download['status']))
    
    # VCC Tab functionality
    def check_vcc_status(self):
        """Check VCC integration status"""
        # Update VCC settings display
        self.vcc_enabled_label.setText("Enabled" if settings.is_vcc_enabled() else "Disabled")
        self.repo_path_label.setText(settings.get_repository_path())
        
        # Enable/disable buttons based on VCC status
        if settings.is_vcc_enabled():
            self.vcc_enable_btn.setEnabled(False)
            self.vcc_disable_btn.setEnabled(True)
            self.add_repo_btn.setEnabled(True)
            self.regen_index_btn.setEnabled(True)
            self.package_all_btn.setEnabled(True)
            self.auto_package_checkbox.setEnabled(True)
            self.auto_package_checkbox.setChecked(settings.get_auto_package_new_items())
        else:
            self.vcc_enable_btn.setEnabled(True)
            self.vcc_disable_btn.setEnabled(False)
            self.add_repo_btn.setEnabled(False)
            self.regen_index_btn.setEnabled(False)
            self.package_all_btn.setEnabled(False)
            self.auto_package_checkbox.setEnabled(False)
        
        # If VCC is not enabled, we're done
        if not settings.is_vcc_enabled():
            self.repo_exists_label.setText("No")
            self.index_valid_label.setText("No")
            self.packages_found_label.setText("0")
            self.overall_status_label.setText("Not configured")
            return
        
        # Check repository status in a worker thread
        self.statusBar.showMessage("Checking VCC integration status...")
        
        worker = Worker(test_vcc_integration, settings.get_repository_path())
        worker.finished.connect(self.display_vcc_status)
        worker.error.connect(self.show_error)
        worker.start()
        
        # Store worker reference
        self.workers.append(worker)
    
    def display_vcc_status(self, status):
        """Display VCC integration status"""
        self.repo_exists_label.setText("Yes" if status['repository_exists'] else "No")
        self.index_valid_label.setText("Yes" if status['index_valid'] else "No")
        self.packages_found_label.setText(str(status['packages_found']))
        self.overall_status_label.setText(status['overall_status'])
        
        # Get packaged items and update table
        self.update_packages_table()
        
        self.statusBar.showMessage("VCC integration status updated.")
    
    def update_packages_table(self):
        """Update the packages table with all packaged items"""
        # Clear the table
        self.packages_table.setRowCount(0)
        
        # Get all packaged items
        packaged_items = self.db.get_packaged_items()
        
        # Populate the table
        for row, item in enumerate(packaged_items):
            self.packages_table.insertRow(row)
            
            # ID
            id_item = QTableWidgetItem(item['item_id'])
            id_item.setData(Qt.ItemDataRole.UserRole, item)  # Store the full item data
            self.packages_table.setItem(row, 0, id_item)
            
            # Title
            title_item = QTableWidgetItem(item['title'])
            self.packages_table.setItem(row, 1, title_item)
            
            # Package ID
            package_id_item = QTableWidgetItem(item.get('package_id', 'Unknown'))
            self.packages_table.setItem(row, 2, package_id_item)
            
            # Actions - would usually be buttons
            actions_item = QTableWidgetItem("Manage")
            self.packages_table.setItem(row, 3, actions_item)
    
    def enable_vcc(self):
        """Enable VCC integration"""
        # Enable VCC integration
        settings.set_vcc_enabled(True)
        settings.ensure_repository_structure()
        settings.save()
        
        # Update UI
        self.check_vcc_status()
        self.statusBar.showMessage("VCC integration enabled.")
        
        # Add activity to dashboard
        self.activity_list.insertItem(0, QListWidgetItem(f"{datetime.now().strftime('%H:%M:%S')} - VCC integration enabled"))
        
        # Generate initial repository index if it doesn't exist
        repo_path = settings.get_repository_path()
        index_path = os.path.join(repo_path, "index.json")
        if not os.path.exists(index_path):
            self.regenerate_index()
    
    def disable_vcc(self):
        """Disable VCC integration"""
        # Disable VCC integration
        settings.set_vcc_enabled(False)
        settings.save()
        
        # Update UI
        self.check_vcc_status()
        self.statusBar.showMessage("VCC integration disabled.")
        
        # Add activity to dashboard
        self.activity_list.insertItem(0, QListWidgetItem(f"{datetime.now().strftime('%H:%M:%S')} - VCC integration disabled"))
    
    def toggle_vcc(self):
        """Toggle VCC integration on/off"""
        if settings.is_vcc_enabled():
            self.disable_vcc()
        else:
            self.enable_vcc()
    
    def toggle_auto_package(self):
        """Toggle auto-packaging of new items"""
        # Update setting
        settings.set_auto_package_new_items(self.auto_package_checkbox.isChecked())
        settings.save()
        
        # Update status
        status = "enabled" if self.auto_package_checkbox.isChecked() else "disabled"
        self.statusBar.showMessage(f"Auto-packaging of new items {status}.")
    
    def regenerate_index(self):
        """Regenerate VCC repository index"""
        # Show message
        self.statusBar.showMessage("Regenerating VCC repository index...")
        
        # Start regenerate process in a worker thread
        worker = Worker(
            generate_repository_index,
            settings.get_repository_path(),
            settings.get_repository_name(),
            settings.get_repository_id(),
            settings.get_repository_author()
        )
        worker.finished.connect(self.regenerate_index_finished)
        worker.error.connect(self.show_error)
        worker.start()
        
        # Store worker reference
        self.workers.append(worker)
    
    def regenerate_index_finished(self, index_path):
        """Handle repository index regeneration completion"""
        self.statusBar.showMessage(f"Repository index regenerated at {index_path}.")
        
        # Add activity to dashboard
        self.activity_list.insertItem(0, QListWidgetItem(f"{datetime.now().strftime('%H:%M:%S')} - VCC repository index regenerated"))
        
        # Update VCC status
        self.check_vcc_status()
    
    def add_repo_to_vcc(self):
        """Add VCC repository to VCC"""
        # Show message
        self.statusBar.showMessage("Opening VCC protocol link...")
        
        # Start process in a worker thread
        worker = Worker(open_vcc_integration, settings.get_repository_path())
        worker.finished.connect(self.add_repo_finished)
        worker.error.connect(self.show_error)
        worker.start()
        
        # Store worker reference
        self.workers.append(worker)
    
    def add_repo_finished(self, success):
        """Handle add repository completion"""
        if success:
            self.statusBar.showMessage("VCC protocol link opened in browser.")
            
            # Add activity to dashboard
            self.activity_list.insertItem(0, QListWidgetItem(f"{datetime.now().strftime('%H:%M:%S')} - VCC repository added to VCC"))
        else:
            self.statusBar.showMessage("Failed to open VCC protocol link.")
            
            repo_path = settings.get_repository_path()
            index_path = os.path.join(repo_path, "index.json")
            file_url = f"file:///{os.path.abspath(index_path).replace(os.sep, '/')}"
            
            QMessageBox.warning(
                self, "VCC Protocol Failed", 
                f"Failed to open VCC protocol link. Please add the repository manually in VCC settings:\n\n{file_url}"
            )
    
    def package_all_items(self):
        """Package all items for VCC"""
        # Get all unpackaged items
        items = self.db.get_all_items()
        unpackaged = [item for item in items if not item.get('is_packaged')]
        
        if not unpackaged:
            QMessageBox.information(self, "No Items", "All items are already packaged.")
            return
        
        # Confirm packaging
        reply = QMessageBox.question(
            self, "Package Items", 
            f"Package {len(unpackaged)} items for VCC?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Show message
        self.statusBar.showMessage(f"Packaging {len(unpackaged)} items...")
        
        # Package each item sequentially
        packaged_count = 0
        for item in unpackaged:
            success = package_item(item, settings.get_repository_path(), self.db)
            if success:
                packaged_count += 1
        
        # Regenerate repository index
        generate_repository_index(
            settings.get_repository_path(),
            settings.get_repository_name(),
            settings.get_repository_id(),
            settings.get_repository_author()
        )
        
        # Update UI
        self.statusBar.showMessage(f"Packaged {packaged_count} items.")
        
        # Add activity to dashboard
        self.activity_list.insertItem(0, QListWidgetItem(f"{datetime.now().strftime('%H:%M:%S')} - Packaged {packaged_count} items for VCC"))
        
        # Update VCC status
        self.check_vcc_status()
    
    def package_item(self, item):
        """Package a single item for VCC"""
        # Show message
        self.statusBar.showMessage(f"Packaging {item['title']}...")
        
        # Start package process in a worker thread
        worker = Worker(package_item, item, settings.get_repository_path(), self.db)
        worker.finished.connect(lambda success: self.package_item_finished(success, item))
        worker.error.connect(self.show_error)
        worker.start()
        
        # Store worker reference
        self.workers.append(worker)
    
    def package_item_finished(self, success, item):
        """Handle package item completion"""
        if success:
            self.statusBar.showMessage(f"Packaged {item['title']} successfully.")
            
            # Regenerate repository index
            generate_repository_index(
                settings.get_repository_path(),
                settings.get_repository_name(),
                settings.get_repository_id(),
                settings.get_repository_author()
            )
            
            # Add activity to dashboard
            self.activity_list.insertItem(0, QListWidgetItem(f"{datetime.now().strftime('%H:%M:%S')} - Packaged {item['title']} for VCC"))
            
            # Update VCC status
            self.check_vcc_status()
        else:
            self.statusBar.showMessage(f"Failed to package {item['title']}.")
    
    # Settings Tab functionality
    def browse_directory(self, line_edit):
        """Browse for a directory and update the line edit"""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            line_edit.setText(directory)
    
    def save_settings(self):
        """Save all settings"""
        # Update settings
        settings.config["repository_path"] = self.vcc_repo_dir_input.text()
        settings.set_repository_name(self.repo_name_input.text())
        settings.set_repository_id(self.repo_id_input.text())
        settings.set_repository_author(self.repo_author_input.text())
        settings.config["download_directory"] = self.downloads_dir_input.text()
        settings.save()
        
        # Update UI
        self.statusBar.showMessage("Settings saved.")
        
        # Add activity to dashboard
        self.activity_list.insertItem(0, QListWidgetItem(f"{datetime.now().strftime('%H:%M:%S')} - Settings updated"))
        
        # Update VCC status if needed
        self.check_vcc_status()
    
    # Utility functions
    def open_folder(self, folder_path):
        """Open a folder in the file explorer"""
        if not folder_path or not os.path.exists(folder_path):
            QMessageBox.warning(self, "Folder Not Found", f"Folder does not exist: {folder_path}")
            return
        
        # Open folder in file explorer
        if sys.platform == "win32":
            os.startfile(folder_path)
        elif sys.platform == "darwin":  # macOS
            import subprocess
            subprocess.run(["open", folder_path])
        else:  # Linux
            import subprocess
            subprocess.run(["xdg-open", folder_path])
    
    def export_data(self):
        """Export data to a file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Data", "", 
            "JSON Files (*.json);;CSV Files (*.csv)"
        )
        if not file_path:
            return
        
        # Get all items
        items = self.db.get_all_items()
        
        # Export based on file extension
        if file_path.endswith(".json"):
            import json
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
        elif file_path.endswith(".csv"):
            import csv
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(["ID", "Title", "URL", "Is Purchased", "Purchase Date", "Is Packaged", "Package ID"])
                # Write data
                for item in items:
                    writer.writerow([
                        item["item_id"],
                        item["title"],
                        item["url"],
                        "Yes" if item.get("is_purchased") else "No",
                        item.get("purchase_date", ""),
                        "Yes" if item.get("is_packaged") else "No",
                        item.get("package_id", "")
                    ])
        
        self.statusBar.showMessage(f"Data exported to {file_path}.")
    
    def show_about_dialog(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About Booth Assets Manager", 
            "Booth Assets Manager v0.3.0\n\n"
            "A tool to manage and organize Booth item assets.\n\n"
            "© 2024 Chaz Dinkle\n"
            "Licensed under the MIT License."
        )
    
    def show_error(self, message):
        """Show error message"""
        self.statusBar.showMessage(f"Error: {message}")
        QMessageBox.critical(self, "Error", message)
    
    def on_tab_changed(self, index):
        """Handle tab change"""
        # Update specific tab content when switching to it
        if index == 0:  # Dashboard
            self.update_dashboard()
        elif index == 2:  # Downloads
            self.check_auth_status()
            self.update_downloads_table()
        elif index == 3:  # VCC
            self.check_vcc_status()
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Clean up any running worker threads
        for worker in self.workers:
            if worker.isRunning():
                worker.terminate()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for a modern look
    window = BoothAssetsManager()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
