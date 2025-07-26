#!/usr/bin/env python3
"""
Simple structure validation for Blue CLI without external dependencies.
"""

import os
import sys
from pathlib import Path


def validate_file_structure():
    """Validate that all required files are present."""
    required_files = [
        'main.py',
        'requirements.txt',
        'README.md',
        'setup.py',
        '.gitignore',
        'agents/__init__.py',
        'agents/navigator.py',
        'agents/observer.py',
        'agents/tool_agents.py',
        'core/__init__.py',
        'core/workspace_graph.py',
        'core/decision_algorithm.py',
        'utils/__init__.py',
        'utils/config_manager.py',
        'utils/error_handler.py'
    ]
    
    missing_files = []
    present_files = []
    
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            present_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    return present_files, missing_files


def validate_python_syntax():
    """Basic syntax validation for Python files."""
    python_files = [
        'main.py',
        'agents/navigator.py',
        'agents/observer.py',
        'agents/tool_agents.py',
        'core/workspace_graph.py',
        'core/decision_algorithm.py',
        'utils/config_manager.py',
        'utils/error_handler.py'
    ]
    
    syntax_ok = []
    syntax_errors = []
    
    for file_path in python_files:
        if not Path(file_path).exists():
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Compile to check syntax
            compile(source, file_path, 'exec')
            syntax_ok.append(file_path)
            
        except SyntaxError as e:
            syntax_errors.append((file_path, str(e)))
        except Exception as e:
            syntax_errors.append((file_path, f"Error reading file: {e}"))
    
    return syntax_ok, syntax_errors


def check_requirements():
    """Check if requirements.txt has expected dependencies."""
    if not Path('requirements.txt').exists():
        return False, "requirements.txt not found"
    
    with open('requirements.txt', 'r') as f:
        requirements = f.read().lower()
    
    expected_deps = ['autogen', 'watchdog', 'requests', 'networkx', 'termcolor', 'tomli', 'openai']
    missing_deps = []
    
    for dep in expected_deps:
        if dep not in requirements:
            missing_deps.append(dep)
    
    if missing_deps:
        return False, f"Missing dependencies: {', '.join(missing_deps)}"
    
    return True, "All expected dependencies present"


def main():
    """Run validation checks."""
    print("🔵 Blue CLI Structure Validation\n")
    
    # Check file structure
    print("📁 Checking file structure...")
    present, missing = validate_file_structure()
    
    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return False
    else:
        print(f"✅ All {len(present)} required files present")
    
    # Check Python syntax
    print("\n🐍 Checking Python syntax...")
    syntax_ok, syntax_errors = validate_python_syntax()
    
    if syntax_errors:
        print("❌ Syntax errors found:")
        for file_path, error in syntax_errors:
            print(f"   {file_path}: {error}")
        return False
    else:
        print(f"✅ All {len(syntax_ok)} Python files have valid syntax")
    
    # Check requirements
    print("\n📦 Checking requirements...")
    req_ok, req_msg = check_requirements()
    
    if not req_ok:
        print(f"❌ {req_msg}")
        return False
    else:
        print(f"✅ {req_msg}")
    
    # Summary
    print("\n🎉 Validation Summary:")
    print("✅ File structure complete")
    print("✅ Python syntax valid")
    print("✅ Dependencies specified")
    
    print("\n🚀 Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Set Anthropic API key: export ANTHROPIC_API_KEY='your-key'")
    print("3. Run Blue CLI: python main.py --dir /path/to/your/project")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)