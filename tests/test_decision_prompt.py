#!/usr/bin/env python3
"""
Test the enhanced decision prompt formatting
"""

from navigator_agent import NavigatorAgent

def test_decision_prompt_formatting():
    """Test that the decision prompt is properly formatted with context"""
    
    navigator = NavigatorAgent(provider="anthropic")
    
    # Create a realistic changes summary
    changes_summary = {
        'buffer_score': 8,
        'priority_level': 'high',
        'processing_reason': 'security_patterns',
        'total_changes': 3,
        'files_affected': 2,
        'changes': [
            {
                'file': 'auth.py',
                'type': 'modified',
                'details': {
                    'lines_changed': '+15/-2',
                    'functions_added': ['authenticate_user', 'validate_token']
                }
            },
            {
                'file': 'security.py', 
                'type': 'created',
                'details': {
                    'lines_changed': '+45/-0',
                    'functions_added': ['encrypt_data', 'generate_hash']
                }
            }
        ]
    }
    
    # Build the decision context (same as navigator does)
    changes_context = navigator._build_change_context(changes_summary)
    buffer_score = changes_summary.get('buffer_score', 0)
    reason = changes_summary.get('processing_reason', 'unknown')
    
    # Get the decision prompt template from config
    limits = navigator.config.get('limits', {})
    decision_prompt_template = limits.get('decision_prompt', 'fallback prompt')
    
    # Format the prompt (same as navigator does)
    decision_prompt = decision_prompt_template.format(
        changes=changes_context,
        context=f"Score: {buffer_score}, Reason: {reason}"
    )
    
    print("🔍 FORMATTED DECISION PROMPT:")
    print("=" * 60)
    print(decision_prompt)
    print("=" * 60)
    
    # Verify the prompt contains key elements
    assert "Blue, an ambient pair programming assistant" in decision_prompt
    assert "DECISION CRITERIA" in decision_prompt
    assert "Security-related code" in decision_prompt
    assert "AVOID commenting on" in decision_prompt
    assert "auth.py" in decision_prompt  # From changes context
    assert "Score: 8, Reason: security_patterns" in decision_prompt
    assert "YES/NO, confidence 1-10" in decision_prompt
    
    print("✅ Decision prompt properly formatted with:")
    print("  - Clear role definition")
    print("  - Specific decision criteria") 
    print("  - Avoidance guidelines")
    print("  - Actual code changes context")
    print("  - Scoring information")
    print("  - Clear response format")
    
    return True

if __name__ == "__main__":
    test_decision_prompt_formatting()
    print("\n🎉 Enhanced decision prompt test PASSED!")