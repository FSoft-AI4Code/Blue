#!/usr/bin/env python3
"""
Setup script for Blue CLI - Jarvis-like workspace pair programming assistant.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
README_PATH = Path(__file__).parent / "README.md"
long_description = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""

# Read requirements
REQUIREMENTS_PATH = Path(__file__).parent / "requirements.txt"
requirements = []
if REQUIREMENTS_PATH.exists():
    requirements = [
        line.strip() 
        for line in REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="blue-cli",
    version="1.0.0",
    description="Jarvis-like workspace pair programming assistant with AutoGen multi-agent orchestration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Blue CLI Team",
    author_email="team@blue-cli.dev",
    url="https://github.com/blue-cli/blue",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "blue=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Tools",
        "Topic :: Utilities",
    ],
    keywords="ai assistant programming pair-programming workspace cli autogen",
    project_urls={
        "Bug Reports": "https://github.com/blue-cli/blue/issues",
        "Source": "https://github.com/blue-cli/blue",
        "Documentation": "https://github.com/blue-cli/blue/blob/main/README.md",
    },
)