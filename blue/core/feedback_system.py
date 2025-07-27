"""
Feedback System

Handles user feedback processing and adaptive threshold learning.
"""

import time
from typing import Dict, Any, List
from datetime import datetime
from termcolor import colored


class FeedbackSystem:
    """Handles user feedback and adaptive threshold learning"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.limits = config.get('limits', {})
        self.feedback_history: List[Dict[str, Any]] = []
        self.current_score_threshold = self.limits.get('score_threshold', 5)
    
    def process_potential_feedback(self, user_input: str, conversation_history: List[Dict[str, Any]]) -> bool:
        """Check if user input is feedback and process it"""
        if not self.limits.get('enable_adaptive_learning', False):
            return False
            
        user_input_lower = user_input.lower().strip()
        
        # Look for feedback keywords
        positive_feedback = any(word in user_input_lower for word in ['good', 'helpful', 'nice', 'thanks', 'useful', 'great'])
        negative_feedback = any(word in user_input_lower for word in ['bad', 'wrong', 'unhelpful', 'annoying', 'stop', 'quiet'])
        
        if not (positive_feedback or negative_feedback):
            return False
        
        # Find the most recent comment we're awaiting feedback for
        current_time = time.time()
        for entry in reversed(conversation_history):
            if (entry.get('role') == 'assistant' and 
                entry.get('awaiting_feedback') and 
                entry.get('feedback_timeout', 0) > current_time):
                
                # Process the feedback
                self._process_feedback(positive_feedback, entry)
                entry['awaiting_feedback'] = False
                
                # Acknowledge feedback
                feedback_type = "positive" if positive_feedback else "negative"
                print(colored(f"[DEBUG] Received {feedback_type} feedback, adjusting thresholds", "green"))
                return True
        
        return False
    
    def _process_feedback(self, is_positive: bool, comment_entry: Dict[str, Any]):
        """Process user feedback and adjust thresholds"""
        try:
            adjustment = self.limits.get('threshold_adjustment', 1)
            min_threshold = self.limits.get('min_score_threshold', 3)
            max_threshold = self.limits.get('max_score_threshold', 10)
            
            # Adjust threshold based on feedback
            if is_positive:
                # Good comment - lower threshold to get more similar comments
                new_threshold = max(min_threshold, self.current_score_threshold - adjustment)
                feedback_msg = f"Lowered threshold from {self.current_score_threshold} to {new_threshold}"
            else:
                # Bad comment - raise threshold to be more selective
                new_threshold = min(max_threshold, self.current_score_threshold + adjustment)
                feedback_msg = f"Raised threshold from {self.current_score_threshold} to {new_threshold}"
            
            self.current_score_threshold = new_threshold
            
            # Log the feedback
            feedback_record = {
                'timestamp': datetime.now(),
                'is_positive': is_positive,
                'comment_score': comment_entry.get('score', 0),
                'comment_reason': comment_entry.get('reason', 'unknown'),
                'old_threshold': self.current_score_threshold + (adjustment if is_positive else -adjustment),
                'new_threshold': new_threshold
            }
            self.feedback_history.append(feedback_record)
            
            print(colored(f"[LEARNING] {feedback_msg}", "magenta"))
            
        except Exception as e:
            print(colored(f"[DEBUG] Error processing feedback: {e}", "red"))
    
    def mark_awaiting_feedback(self, comment_entry: Dict[str, Any]):
        """Mark that we're awaiting feedback on this comment"""
        comment_entry['awaiting_feedback'] = True
        comment_entry['feedback_timeout'] = time.time() + 60  # 1 minute timeout
    
    def get_current_threshold(self) -> int:
        """Get the current adaptive threshold"""
        return self.current_score_threshold
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback statistics"""
        if not self.feedback_history:
            return {
                'total_feedback': 0,
                'positive_feedback': 0,
                'negative_feedback': 0,
                'current_threshold': self.current_score_threshold
            }
        
        positive_count = sum(1 for f in self.feedback_history if f['is_positive'])
        negative_count = len(self.feedback_history) - positive_count
        
        return {
            'total_feedback': len(self.feedback_history),
            'positive_feedback': positive_count,
            'negative_feedback': negative_count,
            'current_threshold': self.current_score_threshold,
            'initial_threshold': self.limits.get('score_threshold', 5)
        }