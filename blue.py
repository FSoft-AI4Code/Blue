#!/usr/bin/env python3
"""
Blue CLI - A Jarvis-like ambient pair programming assistant
Run as: python blue.py --dir /path/to/codebase
"""

import argparse
import sys
import os
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Blue CLI - Ambient pair programming assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--dir",
        type=str,
        required=True,
        help="Path to the codebase directory to monitor"
    )
    
    args = parser.parse_args()
    
    # Validate directory path
    if not os.path.exists(args.dir):
        print(f"Error: Directory '{args.dir}' does not exist.")
        sys.exit(1)
    
    if not os.path.isdir(args.dir):
        print(f"Error: '{args.dir}' is not a directory.")
        sys.exit(1)
    
    # Initialize and start the Blue CLI system
    from blue_cli import BlueCLI
    
    cli = BlueCLI(args.dir)
    cli.start()

if __name__ == "__main__":
    main()