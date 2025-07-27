#!/usr/bin/env python3
"""
Test Script for Blue's Decision-Making Algorithm

This script simulates realistic development scenarios to test Blue's 
enhanced buffering and decision-making capabilities.

Usage:
    python test_file_changes.py --scenario <scenario_name> [--delay <seconds>]

Scenarios:
    - function_development: Simulates adding new functions
    - refactoring: Simulates code refactoring across multiple files  
    - architectural: Simulates architectural changes (new files + modifications)
    - sustained_activity: Simulates rapid development across many files
    - mixed_development: Realistic mixed development patterns
    - all: Run all scenarios sequentially
"""

import os
import time
import argparse
import shutil
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class TestScenarioRunner:
    def __init__(self, test_dir: str = "test_codebase", delay: float = 2.0):
        self.test_dir = Path(test_dir)
        self.delay = delay
        self.created_files = []
        
    def setup_test_environment(self):
        """Create test directory structure"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        
        self.test_dir.mkdir(exist_ok=True)
        
        # Create basic project structure
        subdirs = ["src", "tests", "config", "utils", "models", "api"]
        for subdir in subdirs:
            (self.test_dir / subdir).mkdir(exist_ok=True)
            
        print(f"✅ Test environment created at: {self.test_dir}")
        print(f"🔍 Start Blue monitoring this directory: python blue.py --dir {self.test_dir}")
        print("⏳ Waiting 5 seconds for you to start Blue...")
        time.sleep(5)
    
    def cleanup_test_environment(self):
        """Clean up test files"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        print(f"🧹 Cleaned up test environment")
    
    def create_file(self, filepath: str, content: str):
        """Create a file with given content"""
        full_path = self.test_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(content)
        
        self.created_files.append(str(full_path))
        print(f"📝 Created: {filepath}")
        time.sleep(self.delay)
    
    def modify_file(self, filepath: str, additional_content: str):
        """Modify existing file by appending content"""
        full_path = self.test_dir / filepath
        
        if full_path.exists():
            with open(full_path, 'a') as f:
                f.write(additional_content)
            print(f"✏️  Modified: {filepath}")
        else:
            print(f"❌ File not found: {filepath}")
        
        time.sleep(self.delay)
    
    def wait_with_message(self, seconds: int, message: str):
        """Wait with a descriptive message"""
        print(f"⏸️  {message} (waiting {seconds}s)")
        time.sleep(seconds)

    # Scenario 1: Function Development (Should trigger: function_completion)
    def scenario_function_development(self):
        """Simulate adding new functions - should trigger Blue comments"""
        print("\n🚀 SCENARIO: Function Development")
        print("Expected: Blue should comment when functions are completed")
        
        # Create initial file
        self.create_file("src/auth.py", '''"""
Authentication module
"""

import hashlib
import secrets

''')
        
        # Add first function (should trigger)
        self.modify_file("src/auth.py", '''
def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{password_hash.hex()}"
''')
        
        # Add second function (should trigger)
        self.modify_file("src/auth.py", '''
def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash"""
    salt, password_hash = stored_hash.split(':')
    computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return password_hash == computed_hash.hex()
''')
        
        # Add third function (should trigger)
        self.modify_file("src/auth.py", '''
def generate_token() -> str:
    """Generate secure random token"""
    return secrets.token_urlsafe(32)
''')

    # Scenario 2: Refactoring (Should trigger: sustained_activity)
    def scenario_refactoring(self):
        """Simulate refactoring across multiple files"""
        print("\n🔄 SCENARIO: Refactoring")
        print("Expected: Blue should comment on sustained activity across files")
        
        # Create base files
        self.create_file("src/user.py", '''class User:
    def __init__(self, username):
        self.username = username
''')
        
        self.create_file("src/database.py", '''class Database:
    def connect(self):
        pass
''')
        
        # Refactor user.py
        self.modify_file("src/user.py", '''
    def validate(self):
        return len(self.username) > 3
''')
        
        # Refactor database.py  
        self.modify_file("src/database.py", '''
    def get_user(self, username):
        return None
''')
        
        # Create new service file (architectural change)
        self.create_file("src/user_service.py", '''from .user import User
from .database import Database

class UserService:
    def __init__(self):
        self.db = Database()
''')
        
        # More refactoring
        self.modify_file("src/user_service.py", '''
    def create_user(self, username):
        user = User(username)
        if user.validate():
            return self.db.save_user(user)
        return None
''')

    # Scenario 3: Architectural Changes (Should trigger: architectural_change)
    def scenario_architectural(self):
        """Simulate architectural changes - new files + modifications"""
        print("\n🏗️  SCENARIO: Architectural Changes")
        print("Expected: Blue should comment on architectural implications")
        
        # Create new module structure
        self.create_file("models/__init__.py", "# Models package")
        
        self.create_file("models/user.py", '''"""
User model with enhanced validation
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    username: str
    email: str
    is_active: bool = True
''')
        
        # Create API layer
        self.create_file("api/__init__.py", "# API package")
        
        self.create_file("api/endpoints.py", '''"""
REST API endpoints
"""

from flask import Flask, request, jsonify
from models.user import User

app = Flask(__name__)
''')
        
        # Add endpoints
        self.modify_file("api/endpoints.py", '''

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    user = User(data['username'], data['email'])
    # TODO: Save to database
    return jsonify({'id': 1, 'username': user.username})
''')
        
        # Create configuration
        self.create_file("config/settings.py", '''"""
Application settings
"""

import os

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///app.db')
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
''')

    # Scenario 4: Sustained Activity (Should trigger: sustained_activity)
    def scenario_sustained_activity(self):
        """Simulate rapid development across many files"""
        print("\n⚡ SCENARIO: Sustained Activity")
        print("Expected: Blue should recognize sustained development patterns")
        
        files_and_content = [
            ("utils/helpers.py", '''def format_date(date):
    return date.strftime('%Y-%m-%d')
'''),
            ("utils/validators.py", '''def validate_email(email):
    return '@' in email and '.' in email
'''),
            ("tests/test_user.py", '''import unittest
from models.user import User

class TestUser(unittest.TestCase):
    def test_user_creation(self):
        user = User('john', 'john@example.com')
        self.assertEqual(user.username, 'john')
'''),
            ("tests/test_api.py", '''import unittest
from api.endpoints import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
'''),
            ("src/exceptions.py", '''class UserError(Exception):
    pass

class ValidationError(UserError):
    pass
'''),
        ]
        
        # Create files rapidly
        for filepath, content in files_and_content:
            self.create_file(filepath, content)
        
        # Make modifications to show continued activity
        for filepath, _ in files_and_content[:3]:
            self.modify_file(filepath, f'''
# Updated at {datetime.now().strftime('%H:%M:%S')}
''')

    # Scenario 5: Mixed Development (Realistic scenario)
    def scenario_mixed_development(self):
        """Simulate realistic mixed development patterns"""
        print("\n🎭 SCENARIO: Mixed Development")
        print("Expected: Blue should show intelligent decision-making")
        
        # Start with small changes (should NOT trigger)
        self.create_file("src/constants.py", "VERSION = '1.0.0'")
        self.modify_file("src/constants.py", "\nAPP_NAME = 'TestApp'")
        
        self.wait_with_message(3, "Small changes - Blue should stay quiet")
        
        # Add significant function (should trigger)
        self.create_file("src/crypto.py", '''import hashlib

def secure_hash(data: str) -> str:
    """Generate secure hash of data"""
    return hashlib.sha256(data.encode()).hexdigest()
''')
        
        self.wait_with_message(5, "Function added - Blue should comment")
        
        # Minor modifications (should NOT trigger due to cooldown)
        self.modify_file("src/constants.py", "\nDEBUG = False")
        self.modify_file("src/crypto.py", "\n# TODO: Add salt support")
        
        self.wait_with_message(3, "Minor changes during cooldown - Blue should stay quiet")
        
        # Wait for cooldown to expire
        self.wait_with_message(30, "Waiting for cooldown to expire...")
        
        # Architectural change (should trigger)
        self.create_file("services/email.py", '''"""
Email service
"""

class EmailService:
    def send_notification(self, user_email: str, message: str):
        print(f"Sending to {user_email}: {message}")
''')
        
        self.modify_file("src/crypto.py", '''

def encrypt_email(email: str) -> str:
    """Encrypt email for storage"""
    return secure_hash(email)
''')
        
        self.wait_with_message(5, "Architectural changes - Blue should comment")

    def run_scenario(self, scenario_name: str):
        """Run a specific test scenario"""
        scenarios = {
            'function_development': self.scenario_function_development,
            'refactoring': self.scenario_refactoring,
            'architectural': self.scenario_architectural,
            'sustained_activity': self.scenario_sustained_activity,
            'mixed_development': self.scenario_mixed_development,
        }
        
        if scenario_name not in scenarios:
            print(f"❌ Unknown scenario: {scenario_name}")
            print(f"Available scenarios: {', '.join(scenarios.keys())}")
            return
        
        print(f"\n🎬 Running scenario: {scenario_name}")
        print(f"⏱️  Using {self.delay}s delay between changes")
        print("=" * 50)
        
        scenarios[scenario_name]()
        
        print(f"\n✅ Scenario '{scenario_name}' completed!")
        print("🔍 Check Blue's output to see how it responded")

    def run_all_scenarios(self):
        """Run all scenarios with pauses between them"""
        scenarios = ['function_development', 'refactoring', 'architectural', 'sustained_activity', 'mixed_development']
        
        for i, scenario in enumerate(scenarios):
            self.run_scenario(scenario)
            
            if i < len(scenarios) - 1:
                self.wait_with_message(10, f"Completed scenario {i+1}/{len(scenarios)}. Preparing next scenario...")


def main():
    parser = argparse.ArgumentParser(
        description="Test Blue's decision-making algorithm with realistic file changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python test_file_changes.py --scenario function_development
    python test_file_changes.py --scenario mixed_development --delay 1.5
    python test_file_changes.py --scenario all --delay 1.0
        """
    )
    
    parser.add_argument(
        '--scenario',
        type=str,
        choices=['function_development', 'refactoring', 'architectural', 'sustained_activity', 'mixed_development', 'all'],
        default='mixed_development',
        help='Test scenario to run (default: mixed_development)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Delay between file changes in seconds (default: 2.0)'
    )
    
    parser.add_argument(
        '--test-dir',
        type=str,
        default='test_codebase',
        help='Directory to create test files in (default: test_codebase)'
    )
    
    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Do not clean up test files after completion'
    )
    
    args = parser.parse_args()
    
    runner = TestScenarioRunner(args.test_dir, args.delay)
    
    try:
        runner.setup_test_environment()
        
        if args.scenario == 'all':
            runner.run_all_scenarios()
        else:
            runner.run_scenario(args.scenario)
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"❌ Error running test: {e}")
    finally:
        if not args.no_cleanup:
            input("\n👀 Press Enter to clean up test files...")
            runner.cleanup_test_environment()
        else:
            print(f"\n📁 Test files preserved in: {runner.test_dir}")


if __name__ == "__main__":
    main()