#!/usr/bin/env python3
"""
Automated test for Blue's Navigator Agent dynamic decision making
"""

import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from blue.agents.navigator import NavigatorAgent
from blue.config import get_config

def test_llm_decision_making():
    """Test LLM-based decision making functionality"""
    print("🧠 Testing LLM Decision Making")
    
    # Initialize navigator with anthropic provider
    config = get_config()
    navigator = NavigatorAgent(config, provider="anthropic")
    
    # Test basic initialization
    assert navigator.feedback_system.get_current_threshold() == 5, "Default threshold should be 5"
    print("✅ Navigator initialized with correct threshold")
    
    # Test configuration loading
    assert navigator.config.get('limits', {}).get('enable_llm_decision', False) == True
    print("✅ LLM decision making enabled in config")
    
    # Test threshold adjustment limits
    limits = navigator.config.get('limits', {})
    assert limits.get('min_score_threshold', 3) == 3
    assert limits.get('max_score_threshold', 10) == 10
    print("✅ Threshold limits configured correctly")
    
    return True

def test_decision_parsing():
    """Test LLM decision response parsing"""
    print("\n🎯 Testing Decision Response Parsing")
    
    config = get_config()
    navigator = NavigatorAgent(config, provider="anthropic")
    
    # Test YES responses with confidence
    test_cases = [
        ("YES, confidence 8", True),
        ("NO, confidence 5", False),
        ("Yes, I think this is good timing, confidence 9", True),
        ("No, not a good time, confidence 3", False),
        ("YES confidence: 6", False),  # Below threshold (7)
        ("YES confidence: 7", True),   # At threshold
        ("Maybe, confidence 8", False), # No clear YES
    ]
    
    for response, expected in test_cases:
        result = navigator.decision_engine._parse_decision_response(response)
        assert result == expected, f"Failed for '{response}': expected {expected}, got {result}"
        print(f"✅ Correctly parsed: '{response}' -> {result}")
    
    return True

def test_feedback_processing():
    """Test user feedback processing"""
    print("\n👍 Testing Feedback Processing")
    
    config = get_config()
    navigator = NavigatorAgent(config, provider="anthropic")
    initial_threshold = navigator.feedback_system.get_current_threshold()
    
    # Create a mock comment entry
    comment_entry = {
        'role': 'assistant',
        'content': 'Test comment',
        'score': 6,
        'reason': 'test',
        'awaiting_feedback': True,
        'feedback_timeout': time.time() + 60
    }
    navigator.conversation_history.append(comment_entry)
    
    # Test positive feedback
    is_feedback = navigator.feedback_system.process_potential_feedback("that was good advice", navigator.conversation_history)
    if navigator.config.get('limits', {}).get('enable_adaptive_learning', False):
        assert is_feedback == True, "Should recognize positive feedback"
        assert navigator.feedback_system.get_current_threshold() < initial_threshold, "Threshold should decrease"
        print(f"✅ Positive feedback: threshold {initial_threshold} -> {navigator.feedback_system.get_current_threshold()}")
    else:
        print("⚠️  Adaptive learning disabled in config")
    
    # Test negative feedback 
    navigator.feedback_system.current_score_threshold = initial_threshold  # Reset
    comment_entry['awaiting_feedback'] = True  # Reset
    comment_entry['feedback_timeout'] = time.time() + 60
    
    is_feedback = navigator.feedback_system.process_potential_feedback("that was annoying", navigator.conversation_history)
    if navigator.config.get('limits', {}).get('enable_adaptive_learning', False):
        assert is_feedback == True, "Should recognize negative feedback"
        assert navigator.feedback_system.get_current_threshold() > initial_threshold, "Threshold should increase"
        print(f"✅ Negative feedback: threshold {initial_threshold} -> {navigator.feedback_system.get_current_threshold()}")
    
    return True

def test_scoring_system():
    """Test the scoring system integration"""
    print("\n📊 Testing Scoring System Integration")
    
    config = get_config()
    navigator = NavigatorAgent(config, provider="anthropic")
    
    # Test with different change scenarios
    test_scenarios = [
        {
            'changes_summary': {
                'buffer_score': 8,
                'priority_level': 'high',
                'processing_reason': 'score_threshold',
                'total_changes': 3,
                'files_affected': 2
            },
            'should_comment': True,
            'description': 'High score above threshold'
        },
        {
            'changes_summary': {
                'buffer_score': 3,
                'priority_level': 'low',
                'processing_reason': 'score_threshold',
                'total_changes': 1,
                'files_affected': 1
            },
            'should_comment': False,
            'description': 'Low score below threshold'
        },
        {
            'changes_summary': {
                'buffer_score': 6,
                'priority_level': 'medium',
                'processing_reason': 'function_completion',
                'total_changes': 2,
                'files_affected': 1
            },
            'should_comment': True,
            'description': 'Function completion with good score'
        }
    ]
    
    for scenario in test_scenarios:
        result = navigator._should_generate_comment(scenario['changes_summary'])
        expected = scenario['should_comment']
        assert result == expected, f"Failed for {scenario['description']}: expected {expected}, got {result}"
        print(f"✅ {scenario['description']}: {result}")
    
    return True

def main():
    """Run all tests"""
    print("🚀 BLUE NAVIGATOR DYNAMIC DECISION TESTS")
    print("=" * 50)
    
    tests = [
        test_llm_decision_making,
        test_decision_parsing,
        test_feedback_processing,
        test_scoring_system
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"✅ {test_func.__name__} PASSED\n")
        except Exception as e:
            print(f"❌ {test_func.__name__} FAILED: {e}\n")
    
    print(f"🎉 TESTS COMPLETED: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All dynamic decision making features working correctly!")
        return True
    else:
        print(f"❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)