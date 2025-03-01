from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

# Get the directory where the package is installed
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(PACKAGE_DIR, 'booth.db')

# Create engine and configure base
engine = create_engine(f'sqlite:///{DATABASE_PATH}')
Base = declarative_base()

class Item(Base):
    __tablename__ = 'items'
    
    item_id = Column(String, primary_key=True)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    description = Column(Text)
    folder_path = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # VCC Package fields
    package_id = Column(String)
    is_packaged = Column(Boolean, default=False)
    package_version = Column(String)
    last_packaged = Column(DateTime)
    
    # Purchase information
    is_purchased = Column(Boolean, default=False)
    purchase_date = Column(Text)
    purchase_price = Column(Text)
    last_download_check = Column(DateTime)
    
    # Relationships
    images = relationship("Image", back_populates="item", cascade="all, delete-orphan")
    downloads = relationship("Download", back_populates="item", cascade="all, delete-orphan")

class Image(Base):
    __tablename__ = 'images'
    
    id = Column(Integer, primary_key=True)
    item_id = Column(String, ForeignKey('items.item_id', ondelete='CASCADE'))
    url = Column(Text, nullable=False)
    local_path = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to item
    item = relationship("Item", back_populates="images")

class Download(Base):
    __tablename__ = 'downloads'
    
    id = Column(Integer, primary_key=True)
    item_id = Column(String, ForeignKey('items.item_id', ondelete='CASCADE'))
    filename = Column(Text, nullable=False)
    url = Column(Text)
    local_path = Column(Text, nullable=False)
    file_size = Column(Integer)
    checksum = Column(Text)
    download_date = Column(Text)
    last_attempt = Column(DateTime, default=datetime.utcnow)
    status = Column(Text, default="completed")
    download_count = Column(Integer, default=1)
    
    # Relationship to item
    item = relationship("Item", back_populates="downloads")

class Database:
    def __init__(self):
        # Create tables if they don't exist
        Base.metadata.create_all(engine)
        # Create session factory
        self.Session = sessionmaker(bind=engine)
    
    def add_item(self, item_id: str, title: str, url: str, description: str = None, folder_path: str = None, 
                 images: list = None, package_id: str = None, is_packaged: bool = False, 
                 package_version: str = None, is_purchased: bool = False, purchase_date: str = None, 
                 purchase_price: str = None):
        """Add or update an item and its images in the database."""
        session = self.Session()
        try:
            # Check if item exists
            item = session.query(Item).filter_by(item_id=item_id).first()
            if not item:
                item = Item(
                    item_id=item_id,
                    title=title,
                    url=url,
                    description=description,
                    folder_path=folder_path or f"BoothItems/{item_id}_{self._sanitize_title(title)}",
                    package_id=package_id,
                    is_packaged=is_packaged,
                    package_version=package_version,
                    is_purchased=is_purchased,
                    purchase_date=purchase_date,
                    purchase_price=purchase_price
                )
                session.add(item)
            else:
                # Update existing item
                item.title = title
                item.url = url
                if description is not None:
                    item.description = description
                if folder_path is not None:
                    item.folder_path = folder_path
                
                # Update package info if provided
                if package_id is not None:
                    item.package_id = package_id
                    item.is_packaged = is_packaged
                    item.package_version = package_version
                
                # Update purchase info if provided
                if is_purchased:
                    item.is_purchased = is_purchased
                    if purchase_date is not None:
                        item.purchase_date = purchase_date
                    if purchase_price is not None:
                        item.purchase_price = purchase_price
            
            # Add images if provided
            if images:
                # Clear existing images
                session.query(Image).filter_by(item_id=item_id).delete()
                
                # Add new images
                for img_url, local_path in images:
                    image = Image(
                        item_id=item_id,
                        url=img_url,
                        local_path=local_path
                    )
                    session.add(image)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_item(self, item_id: str, **kwargs):
        """Update specific fields of an item."""
        session = self.Session()
        try:
            item = session.query(Item).filter_by(item_id=item_id).first()
            if not item:
                return False
            
            # Update provided fields
            for key, value in kwargs.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def remove_item(self, item_id: str):
        """Remove an item and its images from the database."""
        session = self.Session()
        try:
            item = session.query(Item).filter_by(item_id=item_id).first()
            if item:
                session.delete(item)  # This will cascade delete related images and downloads
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_package_info(self, item_id: str, package_id: str, package_version: str, is_packaged: bool = True):
        """Update package information for an item."""
        session = self.Session()
        try:
            item = session.query(Item).filter_by(item_id=item_id).first()
            if item:
                item.package_id = package_id
                item.is_packaged = is_packaged
                item.package_version = package_version
                item.last_packaged = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def add_or_update_download(self, item_id: str, filename: str, local_path: str, 
                              url: str = None, file_size: int = None, checksum: str = None, 
                              download_date: str = None, status: str = "completed"):
        """Add or update a download record."""
        session = self.Session()
        try:
            # Check if download exists
            download = session.query(Download).filter_by(
                item_id=item_id, 
                filename=filename
            ).first()
            
            if not download:
                # Create new download record
                download = Download(
                    item_id=item_id,
                    filename=filename,
                    url=url,
                    local_path=local_path,
                    file_size=file_size,
                    checksum=checksum,
                    download_date=download_date,
                    status=status,
                    download_count=1,
                    last_attempt=datetime.utcnow()
                )
                session.add(download)
            else:
                # Update existing download
                download.local_path = local_path
                if url is not None:
                    download.url = url
                if file_size is not None:
                    download.file_size = file_size
                if checksum is not None:
                    download.checksum = checksum
                if download_date is not None:
                    download.download_date = download_date
                download.status = status
                download.download_count += 1
                download.last_attempt = datetime.utcnow()
            
            # Update item's last_download_check
            item = session.query(Item).filter_by(item_id=item_id).first()
            if item:
                item.last_download_check = datetime.utcnow()
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_downloads(self, item_id: str):
        """Get all downloads for an item."""
        session = self.Session()
        try:
            downloads = session.query(Download).filter_by(item_id=item_id).all()
            return [
                {
                    'id': download.id,
                    'filename': download.filename,
                    'url': download.url,
                    'local_path': download.local_path,
                    'file_size': download.file_size,
                    'checksum': download.checksum,
                    'download_date': download.download_date,
                    'status': download.status,
                    'download_count': download.download_count,
                    'last_attempt': download.last_attempt.isoformat() if download.last_attempt else None
                }
                for download in downloads
            ]
        finally:
            session.close()
    
    def get_purchased_items(self):
        """Get all purchased items from the database."""
        session = self.Session()
        try:
            items = session.query(Item).filter_by(is_purchased=True).all()
            return [
                {
                    'item_id': item.item_id,
                    'title': item.title,
                    'url': item.url,
                    'description': item.description,
                    'folder': item.folder_path,
                    'purchase_date': item.purchase_date,
                    'purchase_price': item.purchase_price,
                    'last_download_check': item.last_download_check.isoformat() if item.last_download_check else None,
                    'downloads': [
                        {
                            'filename': download.filename,
                            'local_path': download.local_path,
                            'download_date': download.download_date,
                            'status': download.status
                        }
                        for download in item.downloads
                    ]
                }
                for item in items
            ]
        finally:
            session.close()
    
    def get_item(self, item_id: str):
        """Get an item and its images from the database."""
        session = self.Session()
        try:
            item = session.query(Item).filter_by(item_id=item_id).first()
            if not item:
                return None
            
            # Convert to dictionary format matching current CSV structure
            return {
                'item_id': item.item_id,
                'title': item.title,
                'url': item.url,
                'description': item.description,
                'folder': item.folder_path,
                'images': [img.url for img in item.images],
                'local_images': [img.local_path for img in item.images],
                'package_id': item.package_id,
                'is_packaged': item.is_packaged,
                'package_version': item.package_version,
                'last_packaged': item.last_packaged.isoformat() if item.last_packaged else None,
                'is_purchased': item.is_purchased,
                'purchase_date': item.purchase_date,
                'purchase_price': item.purchase_price,
                'last_download_check': item.last_download_check.isoformat() if item.last_download_check else None,
                'downloads': [
                    {
                        'filename': download.filename,
                        'local_path': download.local_path,
                        'download_date': download.download_date,
                        'status': download.status
                    }
                    for download in item.downloads
                ]
            }
        finally:
            session.close()
    
    def get_all_items(self):
        """Get all items from the database."""
        session = self.Session()
        try:
            items = session.query(Item).all()
            return [
                {
                    'item_id': item.item_id,
                    'title': item.title,
                    'url': item.url,
                    'description': item.description,
                    'folder': item.folder_path,
                    'images': [img.url for img in item.images],
                    'local_images': [img.local_path for img in item.images],
                    'package_id': item.package_id,
                    'is_packaged': item.is_packaged,
                    'package_version': item.package_version,
                    'last_packaged': item.last_packaged.isoformat() if item.last_packaged else None,
                    'is_purchased': item.is_purchased,
                    'purchase_date': item.purchase_date,
                    'purchase_price': item.purchase_price,
                    'last_download_check': item.last_download_check.isoformat() if item.last_download_check else None,
                    'downloads': [
                        {
                            'filename': download.filename,
                            'local_path': download.local_path,
                            'download_date': download.download_date,
                            'status': download.status
                        }
                        for download in item.downloads
                    ]
                }
                for item in items
            ]
        finally:
            session.close()
    
    def get_packaged_items(self):
        """Get all packaged items from the database."""
        session = self.Session()
        try:
            items = session.query(Item).filter_by(is_packaged=True).all()
            return [
                {
                    'item_id': item.item_id,
                    'title': item.title,
                    'url': item.url,
                    'description': item.description,
                    'folder': item.folder_path,
                    'images': [img.url for img in item.images],
                    'local_images': [img.local_path for img in item.images],
                    'package_id': item.package_id,
                    'package_version': item.package_version,
                    'last_packaged': item.last_packaged.isoformat() if item.last_packaged else None
                }
                for item in items
            ]
        finally:
            session.close()
    
    def _sanitize_title(self, title: str):
        """Sanitize a title for use in folder names."""
        import re
        return re.sub(r'[\\/*?:"<>|]', "", title.replace(" ", "_"))
