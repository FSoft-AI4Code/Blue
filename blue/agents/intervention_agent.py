"""
Intervention Agent

LLM-powered agent that decides when to "jump in" and have the NavigatorAgent speak.
Analyzes code changes and determines the right timing for providing insights.
"""

import re
from typing import Dict, Any, Optional
from termcolor import colored

from .base import BaseAgent
from blue.core.llm_client import LLMClient
from blue.core.llm_config import LLMConfigManager


class InterventionAgent(BaseAgent):
    """Agent that decides when the NavigatorAgent should intervene with insights"""
    
    def __init__(self, config: Dict[str, Any], llm_config_manager: LLMConfigManager):
        super().__init__(config)
        self.llm_config_manager = llm_config_manager
        self.llm_client: Optional[LLMClient] = None
        self.limits = config.get('limits', {})
    
    def initialize(self):
        """Initialize the intervention agent"""
        # Initialize LLM client using agent-specific configuration
        self.llm_client = self.llm_config_manager.create_client_for_agent('intervention')
        
        if not self.llm_client or not self.llm_client.is_available():
            agent_info = self.llm_config_manager.get_agent_info('intervention')
            self._log_warning(f"InterventionAgent LLM client ({agent_info['provider'].upper()}) could not be initialized. Using fallback behavior.")
        else:
            agent_info = self.llm_config_manager.get_agent_info('intervention')
            self._log_success(f"InterventionAgent initialized with {agent_info['provider'].upper()} using {agent_info['model']}")
        
        self._initialized = True
    
    def should_intervene(self, changes_summary: Dict[str, Any], changes_context: str) -> bool:
        """Decide if the NavigatorAgent should intervene with insights"""
        
        # If LLM-based decisions are disabled, always allow intervention
        if not self.limits.get('enable_llm_decision', False):
            self._log_debug("LLM decision making disabled, allowing intervention")
            return True
        
        # If no LLM client available, fall back to allowing intervention
        if not self.llm_client or not self.llm_client.is_available():
            self._log_warning("LLM client not available for intervention decision")
            return True
        
        try:
            # Query the LLM for intervention decision
            decision_response = self._query_llm_for_intervention(changes_summary, changes_context)
            
            if decision_response:
                return self._parse_intervention_decision(decision_response)
            
            # Default to not intervening if decision fails
            self._log_debug("LLM decision failed, defaulting to no intervention")
            return False
            
        except Exception as e:
            self._log_error(f"Error in intervention decision: {e}")
            return False  # Conservative default
    
    def _query_llm_for_intervention(self, changes_summary: Dict[str, Any], changes_context: str) -> Optional[str]:
        """Query LLM to decide if now is a good time to intervene"""
        
        # Get the decision prompt template
        decision_prompt_template = self.limits.get('decision_prompt', 
            "Changes: {changes}. Context: {context}. Good time for big-picture input? Answer: YES/NO, confidence 1-10.")
        
        # Build context for decision
        buffer_score = changes_summary.get('buffer_score', 0)
        reason = changes_summary.get('processing_reason', 'unknown')
        priority = changes_summary.get('priority_level', 'low')
        
        # Create enhanced context
        context_info = f"Score: {buffer_score}, Reason: {reason}, Priority: {priority}"
        
        # Format the decision prompt
        decision_prompt = decision_prompt_template.format(
            changes=changes_context,
            context=context_info
        )
        
        # Generate decision using a lightweight call
        messages = [{"role": "user", "content": decision_prompt}]
        system_prompt = "You are an intervention timing assistant. Decide if now is a good time to provide coding insights. Answer briefly with YES/NO and confidence 1-10."
        
        try:
            response = self.llm_client.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=50,
                temperature=0.3
            )
            
            self._log_debug(f"LLM intervention query completed")
            return response
            
        except Exception as e:
            self._log_error(f"Error generating intervention decision: {e}")
            return None
    
    def _parse_intervention_decision(self, response: str) -> bool:
        """Parse LLM intervention decision and check confidence threshold"""
        try:
            response_lower = response.lower()
            self._log_debug(f"LLM Intervention Decision: {response}")
            
            # Extract YES/NO
            has_yes = 'yes' in response_lower
            has_no = 'no' in response_lower
            
            if not has_yes and not has_no:
                self._log_warning("Unclear intervention response, defaulting to no intervention")
                return False
            
            if has_no:
                self._log_debug("LLM explicitly said NO to intervention")
                return False
            
            # Extract confidence (look for numbers 1-10)
            confidence_matches = re.findall(r'\\b([1-9]|10)\\b', response)
            if confidence_matches:
                confidence = int(confidence_matches[-1])  # Take last number found
                confidence_threshold = self.limits.get('confidence_threshold', 7)
                
                decision = has_yes and confidence >= confidence_threshold
                self._log_debug(f"Confidence: {confidence}/{confidence_threshold}, Intervention Decision: {decision}")
                return decision
            
            # Default: if YES but no confidence found, assume medium confidence
            if has_yes:
                self._log_debug("YES response with no confidence found, assuming medium confidence")
                return True
            
            return False
            
        except Exception as e:
            self._log_error(f"Error parsing intervention decision: {e}")
            return False
    
    def analyze_intervention_opportunity(self, changes_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the intervention opportunity and provide reasoning"""
        analysis = {
            'should_intervene': False,
            'confidence': 0,
            'reasoning': [],
            'risk_factors': [],
            'opportunity_factors': []
        }
        
        buffer_score = changes_summary.get('buffer_score', 0)
        reason = changes_summary.get('processing_reason', 'unknown')
        priority = changes_summary.get('priority_level', 'low')
        files_affected = changes_summary.get('files_affected', 0)
        
        # Analyze opportunity factors
        if buffer_score >= self.limits.get('score_threshold', 5):
            analysis['opportunity_factors'].append(f"High change score ({buffer_score})")
            analysis['confidence'] += 3
        
        if priority == 'high':
            analysis['opportunity_factors'].append("High priority changes detected")
            analysis['confidence'] += 3
        elif priority == 'medium':
            analysis['opportunity_factors'].append("Medium priority changes detected")
            analysis['confidence'] += 2
        
        if reason in ['function_completion', 'architectural_change']:
            analysis['opportunity_factors'].append(f"Structural change detected: {reason}")
            analysis['confidence'] += 2
        
        if files_affected >= 3:
            analysis['opportunity_factors'].append(f"Multiple files affected ({files_affected})")
            analysis['confidence'] += 1
        
        # Analyze risk factors (reasons not to intervene)
        if reason == 'idle_timeout':
            analysis['risk_factors'].append("Triggered by idle timeout, may not be urgent")
            analysis['confidence'] -= 1
        
        if buffer_score < 3:
            analysis['risk_factors'].append("Low change score, minimal impact")
            analysis['confidence'] -= 2
        
        if files_affected == 1 and priority == 'low':
            analysis['risk_factors'].append("Single file, low priority change")
            analysis['confidence'] -= 1
        
        # Make final decision based on confidence
        analysis['confidence'] = max(0, min(10, analysis['confidence']))
        analysis['should_intervene'] = analysis['confidence'] >= 5
        
        # Build reasoning
        if analysis['should_intervene']:
            analysis['reasoning'].append("Intervention recommended based on:")
            analysis['reasoning'].extend([f"  • {factor}" for factor in analysis['opportunity_factors']])
        else:
            analysis['reasoning'].append("Intervention not recommended due to:")
            analysis['reasoning'].extend([f"  • {factor}" for factor in analysis['risk_factors']])
        
        return analysis
    
    def get_intervention_stats(self) -> Dict[str, Any]:
        """Get statistics about intervention decisions"""
        # This could be expanded to track decision history
        return {
            'llm_decisions_enabled': self.limits.get('enable_llm_decision', False),
            'confidence_threshold': self.limits.get('confidence_threshold', 7),
            'llm_available': self.llm_client.is_available() if self.llm_client else False
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get intervention agent status"""
        base_status = super().get_status()
        
        # Get agent-specific LLM configuration info
        intervention_info = self.llm_config_manager.get_agent_info('intervention')
        
        base_status.update({
            'llm_available': self.llm_client.is_available() if self.llm_client else False,
            'llm_info': {
                'provider': intervention_info['provider'],
                'model': intervention_info['model'],
                'max_tokens': intervention_info['max_tokens'],
                'temperature': intervention_info['temperature']
            },
            'intervention_config': self.get_intervention_stats()
        })
        return base_status