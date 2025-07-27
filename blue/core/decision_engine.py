"""
Decision Engine

Handles LLM-based dynamic decision making for when to provide coding insights.
"""

import re
from typing import Dict, Any, Optional
from termcolor import colored
from blue.core.llm_client import LLMClient


class DecisionEngine:
    """Handles LLM-based decision making for commenting"""
    
    def __init__(self, llm_client: LLMClient, config: Dict[str, Any]):
        self.llm_client = llm_client
        self.config = config
        self.limits = config.get('limits', {})
    
    def should_comment_via_llm(self, changes_summary: Dict[str, Any], changes_context: str) -> bool:
        """Query LLM to decide if now is a good time to comment"""
        if not self.limits.get('enable_llm_decision', False):
            return True  # Fallback to score-based decision
        
        if not self.llm_client or not self.llm_client.is_available():
            print(colored("[DEBUG] LLM client not available for decision making", "yellow"))
            return True
        
        try:
            decision_response = self._query_llm_for_decision(changes_summary, changes_context)
            if decision_response:
                return self._parse_decision_response(decision_response)
            
            return False  # Default to not commenting if decision fails
            
        except Exception as e:
            print(colored(f"[DEBUG] Error in LLM decision: {e}", "red"))
            return False  # Default to not commenting on error
    
    def _query_llm_for_decision(self, changes_summary: Dict[str, Any], changes_context: str) -> Optional[str]:
        """Query LLM to decide if now is a good time to comment"""
        decision_prompt_template = self.limits.get('decision_prompt', 
            "Changes: {changes}. Context: {context}. Good time for big-picture input? Answer: YES/NO, confidence 1-10.")
        
        # Build context for decision
        buffer_score = changes_summary.get('buffer_score', 0)
        reason = changes_summary.get('processing_reason', 'unknown')
        
        # Create decision prompt
        decision_prompt = decision_prompt_template.format(
            changes=changes_context,
            context=f"Score: {buffer_score}, Reason: {reason}"
        )
        
        # Generate decision using a lightweight call
        messages = [{"role": "user", "content": decision_prompt}]
        system_prompt = "You are a decision assistant. Answer briefly: YES/NO, confidence 1-10."
        
        return self.llm_client.generate_response(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=50,
            temperature=0.3
        )
    
    def _parse_decision_response(self, response: str) -> bool:
        """Parse LLM decision response and check confidence threshold"""
        try:
            response_lower = response.lower()
            print(colored(f"[DEBUG] LLM Decision: {response}", "cyan"))
            
            # Extract YES/NO
            has_yes = 'yes' in response_lower
            has_no = 'no' in response_lower
            
            if not has_yes and not has_no:
                return False  # Unclear response
            
            if has_no:
                return False  # Explicit NO
            
            # Extract confidence (look for numbers 1-10)
            confidence_matches = re.findall(r'\b([1-9]|10)\b', response)
            if confidence_matches:
                confidence = int(confidence_matches[-1])  # Take last number found
                confidence_threshold = self.limits.get('confidence_threshold', 7)
                
                decision = has_yes and confidence >= confidence_threshold
                print(colored(f"[DEBUG] Confidence: {confidence}/{confidence_threshold}, Decision: {decision}", "cyan"))
                return decision
            
            # Default: if YES but no confidence, assume medium confidence
            return has_yes
            
        except Exception as e:
            print(colored(f"[DEBUG] Error parsing decision: {e}", "red"))
            return False