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
    
    # Relationship to images
    images = relationship("Image", back_populates="item", cascade="all, delete-orphan")

class Image(Base):
    __tablename__ = 'images'
    
    id = Column(Integer, primary_key=True)
    item_id = Column(String, ForeignKey('items.item_id', ondelete='CASCADE'))
    url = Column(Text, nullable=False)
    local_path = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to item
    item = relationship("Item", back_populates="images")

class Database:
    def __init__(self):
        # Create tables if they don't exist
        Base.metadata.create_all(engine)
        # Create session factory
        self.Session = sessionmaker(bind=engine)
    
    def add_item(self, item_id: str, title: str, url: str, description: str, folder_path: str, images: list, package_id: str = None, is_packaged: bool = False, package_version: str = None):
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
                    folder_path=folder_path,
                    package_id=package_id,
                    is_packaged=is_packaged,
                    package_version=package_version
                )
                session.add(item)
            else:
                # Update existing item
                item.title = title
                item.url = url
                item.description = description
                item.folder_path = folder_path
                
                # Update package info if provided
                if package_id is not None:
                    item.package_id = package_id
                    item.is_packaged = is_packaged
                    item.package_version = package_version
            
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
    
    def remove_item(self, item_id: str):
        """Remove an item and its images from the database."""
        session = self.Session()
        try:
            item = session.query(Item).filter_by(item_id=item_id).first()
            if item:
                session.delete(item)  # This will cascade delete related images
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
                'last_packaged': item.last_packaged.isoformat() if item.last_packaged else None
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
                    'last_packaged': item.last_packaged.isoformat() if item.last_packaged else None
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
