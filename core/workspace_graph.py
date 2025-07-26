"""
Workspace Context Graph - In-memory workspace context graph managing nodes/edges,
auto-parsing references, manual links, and traversals for insights.
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path

import networkx as nx
from termcolor import colored


class WorkspaceGraph:
    """
    Workspace context graph for managing relationships between:
    - Code files and their dependencies
    - External resources (Jira tickets, GitHub issues, Drive docs)
    - Goals and subtasks 
    - Developer intentions and patterns
    """
    
    def __init__(self):
        # NetworkX graph for storing relationships
        self.graph = nx.DiGraph()
        
        # Node type tracking
        self.nodes_by_type: Dict[str, Set[str]] = {
            'file': set(),
            'goal': set(),
            'subtask': set(),
            'external': set(),
            'reference': set(),
            'pattern': set()
        }
        
        # Change tracking
        self.change_history: List[Dict[str, Any]] = []
        self.last_analysis: Optional[datetime] = None
        
        # Reference patterns for auto-parsing
        self.reference_patterns = {
            'jira': re.compile(r'(?:JIRA-|#)([A-Z]+-\d+)', re.IGNORECASE),
            'github_issue': re.compile(r'(?:GH-|#)(\d+)', re.IGNORECASE),
            'github_pr': re.compile(r'(?:PR-|#PR)(\d+)', re.IGNORECASE),
            'ticket': re.compile(r'(?:TICKET-|#T)(\d+)', re.IGNORECASE),
            'story': re.compile(r'(?:STORY-|#S)(\d+)', re.IGNORECASE)
        }
    
    async def add_file_node(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a file node to the graph."""
        node_id = f"file:{file_path}"
        
        node_data = {
            'type': 'file',
            'path': file_path,
            'name': Path(file_path).name,
            'extension': Path(file_path).suffix,
            'created_at': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat()
        }
        
        if metadata:
            node_data.update(metadata)
        
        self.graph.add_node(node_id, **node_data)
        self.nodes_by_type['file'].add(node_id)
        
        # Auto-parse references in file content
        await self._parse_file_references(node_id, file_path)
        
        # Record change
        self._record_change('add_node', {'node_id': node_id, 'type': 'file'})
        
        return node_id
    
    async def add_goal_node(self, goal: str, subtasks: Optional[List[str]] = None) -> str:
        """Add a goal node and its subtasks."""
        goal_id = f"goal:{hash(goal) & 0x7FFFFFFF}"  # Positive hash
        
        goal_data = {
            'type': 'goal',
            'content': goal,
            'created_at': datetime.now().isoformat(),
            'status': 'active',
            'priority': 'high'
        }
        
        self.graph.add_node(goal_id, **goal_data)
        self.nodes_by_type['goal'].add(goal_id)
        
        # Add subtask nodes and connect them
        if subtasks:
            for i, subtask in enumerate(subtasks):
                subtask_id = await self.add_subtask_node(subtask, goal_id, i)
                self.graph.add_edge(goal_id, subtask_id, relation='has_subtask', order=i)
        
        self._record_change('add_goal', {'goal_id': goal_id, 'subtasks': len(subtasks or [])})
        
        return goal_id
    
    async def add_subtask_node(self, subtask: str, goal_id: str, order: int = 0) -> str:
        """Add a subtask node."""
        subtask_id = f"subtask:{hash(subtask) & 0x7FFFFFFF}"
        
        subtask_data = {
            'type': 'subtask',
            'content': subtask,
            'goal_id': goal_id,
            'order': order,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        self.graph.add_node(subtask_id, **subtask_data)
        self.nodes_by_type['subtask'].add(subtask_id)
        
        return subtask_id
    
    async def add_external_link(self, link_type: str, url: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add an external resource link."""
        try:
            external_id = f"external:{link_type}:{hash(url) & 0x7FFFFFFF}"
            
            external_data = {
                'type': 'external',
                'link_type': link_type,
                'url': url,
                'created_at': datetime.now().isoformat(),
                'last_accessed': None,
                'access_count': 0
            }
            
            if metadata:
                external_data.update(metadata)
            
            self.graph.add_node(external_id, **external_data)
            self.nodes_by_type['external'].add(external_id)
            
            # Auto-link to relevant goals/files based on context
            await self._auto_link_external(external_id, link_type, url)
            
            self._record_change('add_external', {'external_id': external_id, 'type': link_type})
            
            return True
            
        except Exception as e:
            print(colored(f"Error adding external link: {e}", "red"))
            return False
    
    async def add_reference_node(self, ref_type: str, ref_id: str, context: Optional[str] = None) -> str:
        """Add a reference node (auto-parsed from code comments/strings)."""
        reference_id = f"reference:{ref_type}:{ref_id}"
        
        if reference_id in self.graph:
            # Update existing reference
            self.graph.nodes[reference_id]['last_seen'] = datetime.now().isoformat()
            self.graph.nodes[reference_id]['mention_count'] = self.graph.nodes[reference_id].get('mention_count', 0) + 1
        else:
            # Create new reference
            reference_data = {
                'type': 'reference',
                'ref_type': ref_type,
                'ref_id': ref_id,
                'context': context,
                'created_at': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'mention_count': 1
            }
            
            self.graph.add_node(reference_id, **reference_data)
            self.nodes_by_type['reference'].add(reference_id)
        
        return reference_id
    
    async def connect_nodes(self, from_node: str, to_node: str, relation: str, metadata: Optional[Dict[str, Any]] = None):
        """Create a connection between two nodes."""
        edge_data = {
            'relation': relation,
            'created_at': datetime.now().isoformat(),
            'strength': 1.0
        }
        
        if metadata:
            edge_data.update(metadata)
        
        # If edge exists, strengthen it
        if self.graph.has_edge(from_node, to_node):
            current_strength = self.graph.edges[from_node, to_node].get('strength', 1.0)
            edge_data['strength'] = min(current_strength + 0.1, 2.0)
        
        self.graph.add_edge(from_node, to_node, **edge_data)
        
        self._record_change('add_edge', {
            'from': from_node,
            'to': to_node,
            'relation': relation
        })
    
    async def update_file_node(self, file_path: str, metadata: Dict[str, Any]):
        """Update a file node with new metadata."""
        node_id = f"file:{file_path}"
        
        if node_id in self.graph:
            # Update existing node
            self.graph.nodes[node_id].update(metadata)
            self.graph.nodes[node_id]['last_modified'] = datetime.now().isoformat()
            
            # Re-parse references in case content changed
            await self._parse_file_references(node_id, file_path)
            
            self._record_change('update_node', {'node_id': node_id, 'changes': list(metadata.keys())})
        else:
            # Create new node if it doesn't exist
            await self.add_file_node(file_path, metadata)
    
    async def remove_node(self, node_id: str):
        """Remove a node and its connections."""
        if node_id in self.graph:
            node_type = self.graph.nodes[node_id].get('type', 'unknown')
            
            # Remove from type tracking
            if node_type in self.nodes_by_type:
                self.nodes_by_type[node_type].discard(node_id)
            
            # Remove from graph
            self.graph.remove_node(node_id)
            
            self._record_change('remove_node', {'node_id': node_id, 'type': node_type})
    
    async def find_related_nodes(self, node_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Find nodes related to the given node within max_depth."""
        if node_id not in self.graph:
            return []
        
        related = []
        visited = set()
        queue = [(node_id, 0)]
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if current_id in visited or depth > max_depth:
                continue
            
            visited.add(current_id)
            
            if current_id != node_id:  # Don't include the starting node
                node_data = dict(self.graph.nodes[current_id])
                node_data['node_id'] = current_id
                node_data['depth'] = depth
                related.append(node_data)
            
            # Add neighbors to queue
            if depth < max_depth:
                for neighbor in self.graph.neighbors(current_id):
                    if neighbor not in visited:
                        queue.append((neighbor, depth + 1))
                
                # Also check incoming edges
                for predecessor in self.graph.predecessors(current_id):
                    if predecessor not in visited:
                        queue.append((predecessor, depth + 1))
        
        # Sort by relevance (closer nodes first, then by node type priority)
        type_priority = {'goal': 0, 'subtask': 1, 'file': 2, 'reference': 3, 'external': 4}
        related.sort(key=lambda x: (x['depth'], type_priority.get(x.get('type', 'unknown'), 5)))
        
        return related
    
    async def detect_patterns(self) -> List[Dict[str, Any]]:
        """Detect patterns and potential concerns in the graph."""
        patterns = []
        
        # Pattern 1: Orphaned files (no connections)
        orphaned_files = []
        for file_node in self.nodes_by_type['file']:
            if self.graph.degree(file_node) == 0:
                orphaned_files.append(file_node)
        
        if orphaned_files:
            patterns.append({
                'type': 'orphaned_files',
                'description': f'{len(orphaned_files)} files have no connections',
                'concern_level': 'medium',
                'files': orphaned_files[:5]  # Limit to 5 examples
            })
        
        # Pattern 2: Highly connected files (potential coupling issues)
        high_coupling = []
        for file_node in self.nodes_by_type['file']:
            degree = self.graph.degree(file_node)
            if degree > 10:  # Threshold for high coupling
                high_coupling.append((file_node, degree))
        
        if high_coupling:
            high_coupling.sort(key=lambda x: x[1], reverse=True)
            patterns.append({
                'type': 'high_coupling',
                'description': f'{len(high_coupling)} files have high coupling',
                'concern_level': 'high',
                'files': [{'node': node, 'connections': degree} for node, degree in high_coupling[:3]]
            })
        
        # Pattern 3: Unreferenced external resources
        unused_externals = []
        for external_node in self.nodes_by_type['external']:
            # Check if any goals or files reference this external resource
            connected_to_work = any(
                self.graph.nodes[neighbor].get('type') in ['goal', 'file', 'subtask']
                for neighbor in self.graph.neighbors(external_node)
            )
            if not connected_to_work:
                unused_externals.append(external_node)
        
        if unused_externals:
            patterns.append({
                'type': 'unused_externals',
                'description': f'{len(unused_externals)} external resources are not linked to current work',
                'concern_level': 'low',
                'resources': unused_externals[:3]
            })
        
        # Pattern 4: Goals without file connections
        disconnected_goals = []
        for goal_node in self.nodes_by_type['goal']:
            has_file_connection = any(
                self.graph.nodes[neighbor].get('type') == 'file'
                for neighbor in nx.all_neighbors(self.graph, goal_node)
            )
            if not has_file_connection:
                disconnected_goals.append(goal_node)
        
        if disconnected_goals:
            patterns.append({
                'type': 'disconnected_goals',
                'description': f'{len(disconnected_goals)} goals are not connected to any files',
                'concern_level': 'medium',
                'goals': disconnected_goals
            })
        
        return patterns
    
    async def get_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of the workspace graph."""
        # Node counts by type
        node_counts = {node_type: len(nodes) for node_type, nodes in self.nodes_by_type.items()}
        
        # Recent changes (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_changes = [
            change for change in self.change_history[-20:]  # Last 20 changes
            if datetime.fromisoformat(change['timestamp']) > recent_cutoff
        ]
        
        # External links summary
        external_links = []
        for external_node in list(self.nodes_by_type['external'])[:5]:  # Limit to 5
            node_data = self.graph.nodes[external_node]
            external_links.append({
                'type': node_data.get('link_type'),
                'url': node_data.get('url', '')[:50] + '...' if len(node_data.get('url', '')) > 50 else node_data.get('url', '')
            })
        
        # Detect concerns
        concerns = await self.detect_patterns()
        
        return {
            'node_counts': node_counts,
            'edge_count': self.graph.number_of_edges(),
            'recent_changes': recent_changes,
            'external_links': external_links,
            'concerns': [c['description'] for c in concerns if c['concern_level'] in ['medium', 'high']]
        }
    
    async def get_state(self) -> Dict[str, Any]:
        """Get complete graph state for persistence."""
        return {
            'nodes': dict(self.graph.nodes(data=True)),
            'edges': list(self.graph.edges(data=True)),
            'nodes_by_type': {k: list(v) for k, v in self.nodes_by_type.items()},
            'change_history': self.change_history[-50:],  # Keep last 50 changes
            'created_at': datetime.now().isoformat()
        }
    
    async def load_state(self, state_data: Dict[str, Any]):
        """Load graph state from persistence."""
        try:
            # Clear current state
            self.graph.clear()
            for node_set in self.nodes_by_type.values():
                node_set.clear()
            
            # Load nodes
            for node_id, node_data in state_data.get('nodes', {}).items():
                self.graph.add_node(node_id, **node_data)
            
            # Load edges
            for edge_data in state_data.get('edges', []):
                if len(edge_data) >= 3:
                    from_node, to_node, attrs = edge_data[0], edge_data[1], edge_data[2]
                    self.graph.add_edge(from_node, to_node, **attrs)
            
            # Rebuild type tracking
            for node_id, node_data in self.graph.nodes(data=True):
                node_type = node_data.get('type', 'unknown')
                if node_type in self.nodes_by_type:
                    self.nodes_by_type[node_type].add(node_id)
            
            # Load change history
            self.change_history = state_data.get('change_history', [])
            
            print(colored(f"Loaded graph state: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges", "green"))
            
        except Exception as e:
            print(colored(f"Error loading graph state: {e}", "red"))
    
    async def _parse_file_references(self, node_id: str, file_path: str):
        """Parse references from file content and create reference nodes."""
        try:
            if not Path(file_path).exists():
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all reference patterns
            for ref_type, pattern in self.reference_patterns.items():
                matches = pattern.findall(content)
                
                for match in matches:
                    # Create reference node
                    ref_node_id = await self.add_reference_node(ref_type, match, f"Found in {Path(file_path).name}")
                    
                    # Link file to reference
                    await self.connect_nodes(node_id, ref_node_id, 'references')
        
        except Exception as e:
            # Silently ignore file reading errors (binary files, permissions, etc.)
            pass
    
    async def _auto_link_external(self, external_id: str, link_type: str, url: str):
        """Automatically link external resources to relevant goals/files."""
        # Extract identifiers from URL that might match references
        url_lower = url.lower()
        
        # Look for matching reference nodes
        for ref_node in self.nodes_by_type['reference']:
            ref_data = self.graph.nodes[ref_node]
            ref_type = ref_data.get('ref_type', '')
            ref_id = ref_data.get('ref_id', '')
            
            # Check if this external link matches the reference
            if (link_type.lower() == ref_type.lower() or 
                ref_id.lower() in url_lower or
                (link_type == 'jira' and ref_type == 'jira')):
                
                await self.connect_nodes(external_id, ref_node, 'resolves')
                
                # Also connect to files that reference this
                for predecessor in self.graph.predecessors(ref_node):
                    if self.graph.nodes[predecessor].get('type') == 'file':
                        await self.connect_nodes(external_id, predecessor, 'relevant_to')
    
    def _record_change(self, change_type: str, details: Dict[str, Any]):
        """Record a change to the graph."""
        change_record = {
            'type': change_type,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        
        self.change_history.append(change_record)
        
        # Keep history size manageable
        if len(self.change_history) > 200:
            self.change_history = self.change_history[-100:]
    
    @property
    def nodes(self) -> Dict[str, Dict[str, Any]]:
        """Get all nodes in the graph."""
        return dict(self.graph.nodes(data=True))
    
    @property
    def edges(self) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Get all edges in the graph."""
        return list(self.graph.edges(data=True))