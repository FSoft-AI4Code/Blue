#!/usr/bin/env python3
"""
Test Script for Blue's New Scoring-Based Decision Algorithm

This script tests the enhanced scoring system that prevents spam from 
minor edits while ensuring meaningful changes trigger comments.

Usage:
    python test_scoring_system.py [--delay <seconds>]
"""

import os
import time
import argparse
import shutil
from pathlib import Path
from datetime import datetime


class ScoringTestRunner:
    def __init__(self, test_dir: str = "test_scoring", delay: float = 2.0):
        self.test_dir = Path(test_dir)
        self.delay = delay
        
    def setup_test_environment(self):
        """Create test directory structure"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        
        self.test_dir.mkdir(exist_ok=True)
        print(f"✅ Test environment created at: {self.test_dir}")
        print(f"🔍 Start Blue: python blue.py --dir {self.test_dir}")
        print("⏳ Waiting 5 seconds for you to start Blue...")
        time.sleep(5)
    
    def create_file(self, filepath: str, content: str):
        """Create a file with given content"""
        full_path = self.test_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(content)
        
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
    
    def test_spam_prevention(self):
        """Test that minor changes don't trigger comments (score < 5)"""
        print("\n🚫 TEST: Spam Prevention")
        print("Expected: Blue should NOT comment on these minor changes")
        print("Expected scores: 1-2 points each (below threshold of 5)")
        
        # Create initial file (score: 1)
        self.create_file("test.py", "# Initial file\n")
        
        # Add comments (score: 0 each)
        self.modify_file("test.py", "# This is a comment\n")
        self.modify_file("test.py", "# Another comment\n")
        
        # Add print statement (score: 0)
        self.modify_file("test.py", "print('debug message')\n")
        
        # Small variable change (score: 1)
        self.modify_file("test.py", "x = 5\n")
        
        print("📊 Total expected score: ~3 points (below threshold)")
        print("✅ Blue should stay QUIET - these are minor changes")
        
        time.sleep(3)
    
    def test_meaningful_changes(self):
        """Test that meaningful changes trigger comments (score >= 5)"""
        print("\n🎯 TEST: Meaningful Changes")
        print("Expected: Blue SHOULD comment when score reaches 5+")
        
        # Function definition (score: 3 + base 1 = 4)
        self.create_file("auth.py", '''def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()
''')
        
        # Add another function (score: 3 + 1 = 4, total: 8)
        self.modify_file("auth.py", '''
def verify_password(password, hash_value):
    return hash_password(password) == hash_value
''')
        
        print("📊 Expected total score: ~8 points (above threshold of 5)")
        print("✅ Blue SHOULD comment - meaningful functions added!")
        
        time.sleep(5)
    
    def test_security_patterns(self):
        """Test that security-related changes get high scores"""
        print("\n🔒 TEST: Security Patterns")
        print("Expected: Security-related code should get high scores")
        
        # Clear any existing score by waiting
        time.sleep(35)  # Wait for idle timeout to clear buffer
        
        # Security-related function (multiple high-scoring patterns)
        self.create_file("security.py", '''def authenticate_user(username, password, token):
    # Hash the password securely
    password_hash = secure_hash(password)
    
    # Validate the auth token
    if not validate_token(token):
        raise AuthError("Invalid token")
    
    # Check credentials
    return check_credentials(username, password_hash)
''')
        
        print("📊 Expected patterns:")
        print("  - 'def ' (function): +3 points")  
        print("  - 'password' keyword: +3 points (appears 3 times = +9)")
        print("  - 'token' keyword: +2 points (appears 2 times = +4)")
        print("  - 'auth' keyword: +3 points (appears 2 times = +6)")
        print("  - 'hash' keyword: +2 points (appears 2 times = +4)")
        print("📊 Total expected: ~27 points (way above threshold!)")
        print("✅ Blue should comment IMMEDIATELY - high security relevance!")
        
        time.sleep(5)
    
    def test_idle_timeout(self):
        """Test that idle timeout triggers processing"""
        print("\n⏰ TEST: Idle Timeout")
        print("Expected: Blue should comment after 30s of inactivity")
        
        # Make a small change that won't reach score threshold
        self.create_file("small.py", "# Small change\nx = 1\n")
        
        print("📊 Expected score: ~2 points (below threshold)")
        print("⏳ Waiting 35 seconds for idle timeout...")
        print("✅ Blue should comment after 30s due to idle timeout")
        
        time.sleep(35)
    
    def run_all_tests(self):
        """Run all scoring system tests"""
        print("🧪 SCORING SYSTEM TEST SUITE")
        print("=" * 50)
        
        self.test_spam_prevention()
        self.test_meaningful_changes() 
        self.test_security_patterns()
        self.test_idle_timeout()
        
        print("\n🎯 TEST SUMMARY:")
        print("1. Minor changes (comments, prints) should NOT trigger")
        print("2. Function definitions should trigger at score threshold")
        print("3. Security patterns should trigger immediately")
        print("4. Idle timeout should trigger after 30s")
        print("\n✅ All tests completed!")
    
    def cleanup_test_environment(self):
        """Clean up test files"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        print(f"🧹 Cleaned up test environment")


def main():
    parser = argparse.ArgumentParser(
        description="Test Blue's scoring-based decision algorithm"
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Delay between file changes in seconds (default: 2.0)'
    )
    
    args = parser.parse_args()
    
    runner = ScoringTestRunner(delay=args.delay)
    
    try:
        runner.setup_test_environment()
        runner.run_all_tests()
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"❌ Error running test: {e}")
    finally:
        input("\n👀 Press Enter to clean up test files...")
        runner.cleanup_test_environment()


if __name__ == "__main__":
    main()