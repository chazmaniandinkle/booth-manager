from setuptools import setup, find_packages
import os

# Read the README.md file for the long description
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='booth_assets_manager',
    version='0.2.0',
    description='A tool to manage and organize Booth item assets by scraping metadata and images.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Chaz Dinkle',
    author_email='chazmaniandinkle@gmail.com',
    url='https://github.com/chazmaniandinkle/booth-assets-manager',
    project_urls={
        'Bug Tracker': 'https://github.com/chazmaniandinkle/booth-assets-manager/issues',
        'Source Code': 'https://github.com/chazmaniandinkle/booth-assets-manager',
    },
    packages=find_packages(),
    install_requires=[
        'requests',
        'beautifulsoup4',
        'SQLAlchemy>=2.0.27'
    ],
    entry_points={
        'console_scripts': [
            'booth-assets-manager = booth_assets_manager.organizer:main',
            'booth-vcc = booth_assets_manager.vcc_cli:main'
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Utilities',
    ],
    python_requires='>=3.6',
    keywords='booth marketplace assets manager downloader scraper',
)
