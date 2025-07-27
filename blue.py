#!/usr/bin/env python3
"""
Blue CLI - A sophisticated ambient pair programming assistant

A multi-agent system that provides intelligent, proactive coding insights through
LLM-powered reasoning and adaptive learning from user feedback.

Usage:
    python blue.py --dir /path/to/codebase [--provider anthropic] [--config config.toml]

Features:
    - Real-time file monitoring and change analysis
    - LLM-based dynamic decision making  
    - Adaptive learning from user feedback
    - Multi-agent architecture (Observer + Navigator)
    - Pattern-based code scoring system
    - Interactive conversational interface
"""

import argparse
import sys
import os
from pathlib import Path
from termcolor import colored


def validate_directory(path: str) -> str:
    """Validate that the directory path exists and is accessible"""
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(f"Directory '{path}' does not exist.")
    
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError(f"'{path}' is not a directory.")
    
    # Check if directory is readable
    if not os.access(path, os.R_OK):
        raise argparse.ArgumentTypeError(f"Directory '{path}' is not readable.")
    
    return os.path.abspath(path)


def validate_config(path: str) -> str:
    """Validate that the config file exists and is readable"""
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(f"Config file '{path}' does not exist.")
    
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(f"'{path}' is not a file.")
    
    # Check if file is readable
    if not os.access(path, os.R_OK):
        raise argparse.ArgumentTypeError(f"Config file '{path}' is not readable.")
    
    return os.path.abspath(path)


def print_banner():
    """Print the Blue CLI banner"""
    banner = """
🤖 ════════════════════════════════════════════════════════════════════════ 🤖
   ____  _            
  |  _ \\| |_   _  ___ 
  | |_) | | | | |/ _ \\
  |  _ <| | |_| |  __/
  |_| \\_\\_|\\__,_|\\___|  Ambient Pair Programming Assistant
                       
🤖 ════════════════════════════════════════════════════════════════════════ 🤖
"""
    print(colored(banner, "cyan", attrs=['bold']))


def main():
    parser = argparse.ArgumentParser(
        description="Blue CLI - Ambient pair programming assistant with AI-powered insights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python blue.py --dir /path/to/my/project
    python blue.py --dir . --provider openai
    python blue.py --dir /code --config custom.toml --provider anthropic

For more information, visit: https://github.com/your-org/blue
        """
    )
    
    parser.add_argument(
        "--dir",
        type=validate_directory,
        required=True,
        metavar="PATH",
        help="Path to the codebase directory to monitor"
    )
    
    parser.add_argument(
        "--provider",
        type=str,
        choices=["anthropic", "openai"],
        default="anthropic",
        help="LLM provider to use (default: anthropic)"
    )
    
    parser.add_argument(
        "--config",
        type=validate_config,
        metavar="PATH",
        help="Path to custom configuration file (default: config/config.toml)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Blue CLI v1.0.0"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress startup banner and reduce output"
    )
    
    args = parser.parse_args()
    
    # Print banner unless quiet mode
    if not args.quiet:
        print_banner()
    
    # Check for API keys
    provider_env_vars = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY"
    }
    
    env_var = provider_env_vars.get(args.provider)
    if env_var and not os.getenv(env_var):
        print(colored(f"⚠️  Warning: {env_var} environment variable not set.", "yellow"))
        print(colored(f"   You can also set the API key in your config file.", "yellow"))
        print()
    
    # Display startup info
    if not args.quiet:
        print(colored(f"📁 Monitoring directory: {args.dir}", "green"))
        print(colored(f"🧠 LLM Provider: {args.provider.upper()}", "green"))
        if args.config:
            print(colored(f"⚙️  Config file: {args.config}", "green"))
        print()
    
    try:
        # Initialize and start the Blue CLI system
        from blue_cli import BlueCLI
        
        cli = BlueCLI(args.dir, args.provider, args.config)
        cli.start()
        
    except KeyboardInterrupt:
        print(colored("\\n👋 Goodbye! Thanks for coding with Blue!", "cyan"))
        sys.exit(0)
    except ImportError as e:
        print(colored(f"❌ Import error: {e}", "red"))
        print(colored("   Make sure all dependencies are installed: pip install -r requirements.txt", "yellow"))
        sys.exit(1)
    except Exception as e:
        print(colored(f"❌ Error starting Blue CLI: {e}", "red"))
        sys.exit(1)


if __name__ == "__main__":
    main()