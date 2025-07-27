"""
Feedback Processor

Processes user feedback on assistant messages and manages adaptive learning.
Detects positive/negative feedback and adjusts system behavior accordingly.
"""

import time
from typing import Dict, Any, List
from datetime import datetime
from termcolor import colored


class FeedbackProcessor:
    """Processes user feedback and manages adaptive threshold learning"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.limits = config.get('limits', {})
        
        # Feedback state
        self.feedback_history: List[Dict[str, Any]] = []
        self.current_score_threshold = self.limits.get('score_threshold', 5)
        
        # Feedback detection patterns
        self.positive_keywords = ['good', 'helpful', 'nice', 'thanks', 'useful', 'great', 'awesome', 'perfect', 'excellent', 'spot on']
        self.negative_keywords = ['bad', 'wrong', 'unhelpful', 'annoying', 'stop', 'quiet', 'too much', 'spam', 'unnecessary']
    
    def process_potential_feedback(self, user_input: str, conversation_history: List[Dict[str, Any]]) -> bool:
        """Check if user input is feedback and process it"""
        
        # Only process feedback if adaptive learning is enabled
        if not self.limits.get('enable_adaptive_learning', False):
            return False
            
        user_input_lower = user_input.lower().strip()
        
        # Look for feedback keywords
        positive_feedback = any(word in user_input_lower for word in self.positive_keywords)
        negative_feedback = any(word in user_input_lower for word in self.negative_keywords)
        
        if not (positive_feedback or negative_feedback):
            return False
        
        # Find the most recent assistant message we're awaiting feedback for
        current_time = time.time()
        for entry in reversed(conversation_history):
            if (entry.get('role') == 'assistant' and 
                entry.get('awaiting_feedback') and 
                entry.get('feedback_timeout', 0) > current_time):
                
                # Process the feedback
                self._process_feedback(positive_feedback, entry, user_input)
                entry['awaiting_feedback'] = False
                
                # Log the feedback processing
                feedback_type = "positive" if positive_feedback else "negative"
                print(colored(f"[FEEDBACK] Received {feedback_type} feedback, adjusting behavior", "magenta"))
                
                return True
        
        return False
    
    def _process_feedback(self, is_positive: bool, comment_entry: Dict[str, Any], original_input: str):
        """Process user feedback and adjust thresholds"""
        try:
            adjustment = self.limits.get('threshold_adjustment', 1)
            min_threshold = self.limits.get('min_score_threshold', 3)
            max_threshold = self.limits.get('max_score_threshold', 10)
            
            old_threshold = self.current_score_threshold
            
            # Adjust threshold based on feedback
            if is_positive:
                # Good comment - lower threshold to get more similar comments
                new_threshold = max(min_threshold, self.current_score_threshold - adjustment)
                feedback_msg = f"Lowered threshold from {old_threshold} to {new_threshold} (will comment more)"
            else:
                # Bad comment - raise threshold to be more selective
                new_threshold = min(max_threshold, self.current_score_threshold + adjustment)
                feedback_msg = f"Raised threshold from {old_threshold} to {new_threshold} (will comment less)"
            
            self.current_score_threshold = new_threshold
            
            # Create feedback record
            feedback_record = {
                'timestamp': datetime.now(),
                'is_positive': is_positive,
                'original_input': original_input,
                'comment_score': comment_entry.get('score', 0),
                'comment_reason': comment_entry.get('reason', 'unknown'),
                'comment_type': comment_entry.get('type', 'unknown'),
                'old_threshold': old_threshold,
                'new_threshold': new_threshold,
                'comment_content': comment_entry.get('content', '')[:100] + '...' if len(comment_entry.get('content', '')) > 100 else comment_entry.get('content', '')
            }
            self.feedback_history.append(feedback_record)
            
            print(colored(f"[LEARNING] {feedback_msg}", "blue"))
            
        except Exception as e:
            print(colored(f"[ERROR] Error processing feedback: {e}", "red"))
    
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
                'current_threshold': self.current_score_threshold,
                'initial_threshold': self.limits.get('score_threshold', 5),
                'threshold_change': 0
            }
        
        positive_count = sum(1 for f in self.feedback_history if f['is_positive'])
        negative_count = len(self.feedback_history) - positive_count
        initial_threshold = self.limits.get('score_threshold', 5)
        
        return {
            'total_feedback': len(self.feedback_history),
            'positive_feedback': positive_count,
            'negative_feedback': negative_count,
            'current_threshold': self.current_score_threshold,
            'initial_threshold': initial_threshold,
            'threshold_change': self.current_score_threshold - initial_threshold,
            'last_feedback_time': self.feedback_history[-1]['timestamp'].isoformat() if self.feedback_history else None
        }
    
    def get_recent_feedback(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent feedback entries"""
        return self.feedback_history[-limit:] if self.feedback_history else []
    
    def analyze_feedback_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in feedback history"""
        if not self.feedback_history:
            return {'analysis': 'No feedback history available'}
        
        analysis = {
            'total_entries': len(self.feedback_history),
            'positive_ratio': 0,
            'negative_ratio': 0,
            'common_triggers': {},
            'threshold_trend': 'stable',
            'effectiveness': 'unknown'
        }
        
        positive_count = sum(1 for f in self.feedback_history if f['is_positive'])
        total_count = len(self.feedback_history)
        
        analysis['positive_ratio'] = positive_count / total_count if total_count > 0 else 0
        analysis['negative_ratio'] = 1 - analysis['positive_ratio']
        
        # Analyze what triggers feedback
        reason_feedback = {}
        for entry in self.feedback_history:
            reason = entry.get('comment_reason', 'unknown')
            if reason not in reason_feedback:
                reason_feedback[reason] = {'positive': 0, 'negative': 0}
            
            if entry['is_positive']:
                reason_feedback[reason]['positive'] += 1
            else:
                reason_feedback[reason]['negative'] += 1
        
        analysis['common_triggers'] = reason_feedback
        
        # Analyze threshold trend
        if len(self.feedback_history) >= 3:
            recent_thresholds = [f['new_threshold'] for f in self.feedback_history[-3:]]
            if all(t <= recent_thresholds[0] for t in recent_thresholds):
                analysis['threshold_trend'] = 'decreasing'
            elif all(t >= recent_thresholds[0] for t in recent_thresholds):
                analysis['threshold_trend'] = 'increasing'  
            else:
                analysis['threshold_trend'] = 'fluctuating'
        
        # Simple effectiveness measure
        if analysis['positive_ratio'] > 0.6:
            analysis['effectiveness'] = 'good'
        elif analysis['positive_ratio'] > 0.4:
            analysis['effectiveness'] = 'moderate'
        else:
            analysis['effectiveness'] = 'needs_improvement'
        
        return analysis
    
    def reset_threshold(self):
        """Reset threshold to initial value"""
        initial_threshold = self.limits.get('score_threshold', 5)
        old_threshold = self.current_score_threshold
        self.current_score_threshold = initial_threshold
        
        print(colored(f"[LEARNING] Reset threshold from {old_threshold} to {initial_threshold}", "yellow"))
    
    def clear_feedback_history(self):
        """Clear feedback history"""
        self.feedback_history.clear()
        self.reset_threshold()
    
    def export_feedback_data(self) -> Dict[str, Any]:
        """Export feedback data for analysis"""
        return {
            'feedback_history': [
                {
                    'timestamp': entry['timestamp'].isoformat(),
                    'is_positive': entry['is_positive'],
                    'threshold_change': entry['new_threshold'] - entry['old_threshold'],
                    'comment_reason': entry['comment_reason'],
                    'comment_type': entry['comment_type']
                }
                for entry in self.feedback_history
            ],
            'current_state': self.get_feedback_stats(),
            'analysis': self.analyze_feedback_patterns()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get feedback processor status"""
        return {
            'name': 'FeedbackProcessor',
            'adaptive_learning_enabled': self.limits.get('enable_adaptive_learning', False),
            'current_threshold': self.current_score_threshold,
            'feedback_entries': len(self.feedback_history),
            'stats': self.get_feedback_stats()
        }