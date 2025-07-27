#!/usr/bin/env python3
"""
Test Script for Blue's Dynamic Decision Making System

This script tests the LLM-based decision making and adaptive learning features.

Usage:
    python test_dynamic_decisions.py [--delay <seconds>]
"""

import os
import time
import argparse
import shutil
from pathlib import Path
from datetime import datetime


class DynamicDecisionTestRunner:
    def __init__(self, test_dir: str = "test_dynamic", delay: float = 3.0):
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
    
    def wait_for_user_action(self, message: str, seconds: int = 10):
        """Wait for user to perform an action"""
        print(f"\n👀 {message}")
        print(f"⏳ Waiting {seconds} seconds...")
        time.sleep(seconds)
    
    def test_llm_decision_making(self):
        """Test LLM-based decision making"""
        print("\n🧠 TEST: LLM Decision Making")
        print("Expected: Blue queries LLM before commenting")
        print("Look for [DEBUG] LLM Decision: YES/NO, confidence X")
        
        # Create a borderline case that might trigger LLM decision
        self.create_file("service.py", '''def process_data(data):
    # This is a medium-importance function
    results = []
    for item in data:
        if validate_item(item):
            results.append(transform_item(item))
    return results
''')
        
        print("📊 Expected: Score ~4-6 points (borderline case)")
        print("🧠 Blue should ask LLM: 'Good time for big-picture input?'")
        print("✅ Watch for LLM decision process in debug output")
        
        time.sleep(8)
    
    def test_high_confidence_comment(self):
        """Test high-confidence scenario that should comment"""
        print("\n✅ TEST: High Confidence Scenario")
        print("Expected: LLM says YES with high confidence")
        
        # Create high-value security-related code
        self.create_file("auth.py", '''def authenticate_user(username, password, token):
    # Security-critical authentication function
    if not validate_token(token):
        raise AuthenticationError("Invalid token")
    
    password_hash = secure_hash(password)
    user = get_user_by_credentials(username, password_hash)
    
    if not user:
        log_failed_attempt(username)
        raise AuthenticationError("Invalid credentials")
    
    return create_session_token(user)
''')
        
        print("📊 Expected: High score (~15+ points from security patterns)")
        print("🧠 LLM should decide: YES, confidence 8-10")
        print("✅ Blue should comment on security implementation")
        
        self.wait_for_user_action("Check if Blue commented on the security code", 8)
    
    def test_positive_feedback(self):
        """Test positive feedback and threshold adjustment"""
        print("\n👍 TEST: Positive Feedback")
        print("Action needed: After Blue's next comment, type 'good' or 'helpful'")
        
        # Create another function to trigger a comment
        self.modify_file("auth.py", '''

def validate_session(session_token):
    # Validate user session token
    try:
        payload = decode_jwt(session_token)
        return verify_user_session(payload['user_id'])
    except JWTError:
        return False
''')
        
        print("📊 Expected: Should trigger another comment")
        print("👍 After Blue comments, type 'good' or 'thanks'")
        print("🎯 Expected: Threshold should decrease (easier to comment)")
        print("🔍 Look for: [LEARNING] Lowered threshold from X to Y")
        
        self.wait_for_user_action("Type positive feedback after Blue comments", 15)
    
    def test_negative_feedback(self):
        """Test negative feedback and threshold adjustment"""
        print("\n👎 TEST: Negative Feedback")
        print("Action needed: After Blue's next comment, type 'bad' or 'annoying'")
        
        # Create a smaller change that should now comment (due to lowered threshold)
        self.modify_file("service.py", '''

def log_processing_stats(count):
    print(f"Processed {count} items")
''')
        
        print("📊 Expected: Should comment due to lowered threshold")
        print("👎 After Blue comments, type 'bad' or 'stop'")
        print("🎯 Expected: Threshold should increase (harder to comment)")
        print("🔍 Look for: [LEARNING] Raised threshold from X to Y")
        
        self.wait_for_user_action("Type negative feedback after Blue comments", 15)
    
    def test_adaptive_behavior(self):
        """Test that Blue learned from feedback"""
        print("\n🎓 TEST: Adaptive Behavior")
        print("Expected: Blue should be more selective now (higher threshold)")
        
        # Create similar changes to before
        self.create_file("utils.py", '''def format_output(data):
    return json.dumps(data, indent=2)

def save_to_file(data, filename):
    with open(filename, 'w') as f:
        f.write(format_output(data))
''')
        
        print("📊 Expected: Lower score changes")
        print("🎯 With raised threshold, Blue should be quieter")
        print("✅ Blue learned from your feedback and adapted!")
        
        time.sleep(8)
    
    def test_confidence_threshold(self):
        """Test edge cases around confidence threshold"""
        print("\n🎯 TEST: Confidence Threshold Edge Cases")
        print("Expected: Test borderline confidence decisions")
        
        # Create a medium-complexity change
        self.create_file("database.py", '''class DatabaseConnection:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connection = None
    
    def connect(self):
        self.connection = create_connection(self.host, self.port)
        return self.connection is not None
''')
        
        print("📊 Expected: Medium score, might be borderline for LLM")
        print("🧠 LLM might decide: YES, confidence 6-7 (near threshold)")
        print("🎯 Test how Blue handles confidence right at threshold")
        
        time.sleep(8)
    
    def run_all_tests(self):
        """Run all dynamic decision making tests"""
        print("🚀 DYNAMIC DECISION MAKING TEST SUITE")
        print("=" * 60)
        print("This will test:")
        print("1. 🧠 LLM-based decision making")
        print("2. 🎯 Confidence threshold logic") 
        print("3. 👍👎 User feedback processing")
        print("4. 🎓 Adaptive threshold learning")
        print("5. 🔄 Behavioral adaptation")
        print("\n⚠️  IMPORTANT: You need to interact by giving feedback!")
        
        input("Press Enter when Blue is running and ready...")
        
        self.test_llm_decision_making()
        self.test_high_confidence_comment()
        self.test_positive_feedback()
        self.test_negative_feedback()
        self.test_adaptive_behavior()
        self.test_confidence_threshold()
        
        print("\n🎉 DYNAMIC DECISION TESTS COMPLETED!")
        print("\nWhat you should have observed:")
        print("✅ LLM decision queries with confidence scores")
        print("✅ Threshold adjustments based on your feedback")
        print("✅ Blue becoming more/less talkative based on learning")
        print("✅ Different behavior after positive vs negative feedback")
        
    def cleanup_test_environment(self):
        """Clean up test files"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        print(f"🧹 Cleaned up test environment")


def main():
    parser = argparse.ArgumentParser(
        description="Test Blue's dynamic decision making and adaptive learning"
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=3.0,
        help='Delay between file changes in seconds (default: 3.0)'
    )
    
    args = parser.parse_args()
    
    runner = DynamicDecisionTestRunner(delay=args.delay)
    
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