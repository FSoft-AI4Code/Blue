"""
Blue - Ambient Pair Programming Assistant

A sophisticated ambient intelligence system that provides proactive coding insights
through multi-agent architecture and adaptive learning.
"""

__version__ = "1.0.0"
__author__ = "Blue Team"

from blue.agents.navigator_agent import NavigatorAgent
from blue.monitoring.codebase_monitor import CodebaseMonitor

__all__ = ["NavigatorAgent", "CodebaseMonitor"]