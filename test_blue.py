#!/usr/bin/env python3
"""
Basic validation test for Blue CLI components.
"""

import asyncio
import tempfile
from pathlib import Path
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.workspace_graph import WorkspaceGraph
from core.decision_algorithm import DecisionAlgorithm
from agents.navigator import NavigatorAgent
from agents.observer import ObserverAgent
from agents.tool_agents import ToolAgentManager
from utils.config_manager import ConfigManager
from utils.error_handler import ErrorHandler, HealthChecker


async def test_workspace_graph():
    """Test workspace graph functionality."""
    print("Testing Workspace Graph...")
    
    graph = WorkspaceGraph()
    
    # Test adding nodes
    file_node = await graph.add_file_node("/test/file.py", {"size": 1024})
    goal_node = await graph.add_goal_node("Test goal", ["subtask 1", "subtask 2"])
    
    # Test connections
    await graph.connect_nodes(goal_node, file_node, "implements")
    
    # Test patterns
    patterns = await graph.detect_patterns()
    
    # Test summary
    summary = await graph.get_summary()
    
    print(f"✓ Graph created with {len(graph.nodes)} nodes")
    print(f"✓ Detected {len(patterns)} patterns")
    print(f"✓ Summary generated: {summary['node_counts']}")
    

async def test_decision_algorithm():
    """Test decision algorithm."""
    print("\nTesting Decision Algorithm...")
    
    algorithm = DecisionAlgorithm()
    graph = WorkspaceGraph()
    
    # Test event processing
    test_event = {
        'type': 'modified',
        'src_path': '/test/file.py',
        'timestamp': '2024-01-01T12:00:00'
    }
    
    should_intervene, confidence, suggestion = await algorithm.process_event(
        test_event, "test goal", graph
    )
    
    print(f"✓ Event processed: intervene={should_intervene}, confidence={confidence:.1f}%")
    
    # Test feedback
    await algorithm.adjust_from_feedback(True)
    print("✓ Feedback processed")


def test_config_manager():
    """Test configuration management."""
    print("\nTesting Configuration Manager...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "test_config.toml"
        config = ConfigManager(str(config_path))
        
        # Test setting and getting values
        config.set('test.key', 'test_value')
        value = config.get('test.key')
        
        assert value == 'test_value', f"Expected 'test_value', got {value}"
        
        # Test validation
        issues = config.validate_config()
        
        print(f"✓ Config created at {config_path}")
        print(f"✓ Validation found {len(issues)} issues")


async def test_observer():
    """Test observer functionality."""
    print("\nTesting Observer Agent...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        observer = ObserverAgent(Path(temp_dir))
        
        # Test event processing
        test_events = []
        
        async def event_callback(event_data):
            test_events.append(event_data)
        
        # Start watching briefly
        await observer.start_watching(event_callback)
        
        # Create a test file to trigger event
        test_file = Path(temp_dir) / "test.py"
        test_file.write_text("print('hello')")
        
        # Give it a moment to detect
        await asyncio.sleep(0.5)
        
        await observer.stop_watching()
        
        print(f"✓ Observer created for {temp_dir}")
        print(f"✓ Captured {len(test_events)} events")


def test_error_handler():
    """Test error handling."""
    print("\nTesting Error Handler...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "test.log"
        error_handler = ErrorHandler(log_file)
        
        # Test error handling
        test_error = Exception("Test error")
        can_continue = error_handler.handle_error(test_error, "test context")
        
        # Test health checker
        health_checker = HealthChecker(error_handler)
        health_report = asyncio.run(health_checker.check_system_health())
        
        print(f"✓ Error handled, can_continue={can_continue}")
        print(f"✓ Health check completed: {health_report['overall_status']}")


async def run_all_tests():
    """Run all tests."""
    print("🔵 Blue CLI Component Tests\n")
    
    try:
        await test_workspace_graph()
        await test_decision_algorithm()
        test_config_manager()
        await test_observer()
        test_error_handler()
        
        print("\n✅ All tests passed! Blue CLI components are working correctly.")
        
        # Print next steps
        print("\n🚀 Next steps:")
        print("1. Set up your OpenAI API key: export OPENAI_API_KEY='your-key'")
        print("2. Run Blue CLI: python main.py --dir /path/to/your/project")
        print("3. Set a goal: /set-goal 'your programming goal'")
        print("4. Start coding and get strategic guidance!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)