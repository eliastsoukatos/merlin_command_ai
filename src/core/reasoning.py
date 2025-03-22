"""
Reasoning Module

This module implements a multi-step reasoning system that allows Merlin to break down
complex tasks into logical steps, execute tools in sequence, and synthesize results.
"""

import json
from typing import Dict, List, Any, Optional, Union

class ReasoningStep:
    """Represents a single step in a reasoning chain"""
    
    def __init__(self, 
                 step_id: int, 
                 description: str, 
                 tool_name: Optional[str] = None,
                 tool_args: Optional[Dict[str, Any]] = None):
        """
        Initialize a reasoning step
        
        Args:
            step_id: Unique identifier for this step
            description: Description of what this step does
            tool_name: Name of the tool to execute (if any)
            tool_args: Arguments for the tool
        """
        self.step_id = step_id
        self.description = description
        self.tool_name = tool_name
        self.tool_args = tool_args or {}
        self.result = None
        self.is_completed = False
        
    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            "step_id": self.step_id,
            "description": self.description,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "result": self.result,
            "is_completed": self.is_completed
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'ReasoningStep':
        """Create from dictionary representation"""
        step = cls(
            step_id=data["step_id"],
            description=data["description"],
            tool_name=data.get("tool_name"),
            tool_args=data.get("tool_args", {})
        )
        step.result = data.get("result")
        step.is_completed = data.get("is_completed", False)
        return step
        
    def set_result(self, result: Any) -> None:
        """Set the result of executing this step"""
        self.result = result
        self.is_completed = True


class ReasoningChain:
    """Manages a chain of reasoning steps"""
    
    def __init__(self, query: str):
        """
        Initialize a reasoning chain
        
        Args:
            query: The original user query that initiated this chain
        """
        self.query = query
        self.steps: List[ReasoningStep] = []
        self.current_step_idx = 0
        self.is_completed = False
        self.final_response = None
        
    def add_step(self, description: str, tool_name: Optional[str] = None, 
                 tool_args: Optional[Dict[str, Any]] = None) -> ReasoningStep:
        """
        Add a new step to the chain
        
        Args:
            description: Description of what this step does
            tool_name: Name of the tool to execute (if any)
            tool_args: Arguments for the tool
            
        Returns:
            The created step
        """
        step_id = len(self.steps)
        step = ReasoningStep(step_id, description, tool_name, tool_args)
        self.steps.append(step)
        return step
        
    def get_current_step(self) -> Optional[ReasoningStep]:
        """Get the current step in the chain"""
        if 0 <= self.current_step_idx < len(self.steps):
            return self.steps[self.current_step_idx]
        return None
        
    def advance(self) -> bool:
        """
        Advance to the next step in the chain
        
        Returns:
            True if there are more steps, False if chain is complete
        """
        self.current_step_idx += 1
        if self.current_step_idx >= len(self.steps):
            self.is_completed = True
            return False
        return True
        
    def get_context(self) -> Dict:
        """
        Get the current context of the reasoning chain
        
        Returns:
            A dictionary with the chain's context
        """
        completed_steps = []
        for step in self.steps[:self.current_step_idx]:
            if step.is_completed:
                completed_steps.append(step.to_dict())
                
        return {
            "query": self.query,
            "completed_steps": completed_steps,
            "current_step_idx": self.current_step_idx,
            "is_completed": self.is_completed
        }
        
    def to_dict(self) -> Dict:
        """Convert to dictionary representation"""
        return {
            "query": self.query,
            "steps": [step.to_dict() for step in self.steps],
            "current_step_idx": self.current_step_idx,
            "is_completed": self.is_completed,
            "final_response": self.final_response
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'ReasoningChain':
        """Create from dictionary representation"""
        chain = cls(query=data["query"])
        chain.steps = [ReasoningStep.from_dict(step_data) for step_data in data["steps"]]
        chain.current_step_idx = data["current_step_idx"]
        chain.is_completed = data["is_completed"]
        chain.final_response = data.get("final_response")
        return chain
        
    def complete(self, final_response: str) -> None:
        """
        Mark the chain as completed with a final response
        
        Args:
            final_response: Final response to the user
        """
        self.is_completed = True
        self.final_response = final_response


class ReasoningEngine:
    """Manages execution of reasoning chains"""
    
    def __init__(self):
        """Initialize the reasoning engine"""
        self.active_chains: Dict[str, ReasoningChain] = {}
        
    def create_chain(self, query: str) -> str:
        """
        Create a new reasoning chain
        
        Args:
            query: The user query to reason about
            
        Returns:
            Chain ID
        """
        import uuid
        chain_id = f"chain_{uuid.uuid4().hex[:8]}"
        self.active_chains[chain_id] = ReasoningChain(query)
        return chain_id
        
    def get_chain(self, chain_id: str) -> Optional[ReasoningChain]:
        """
        Get a reasoning chain by ID
        
        Args:
            chain_id: ID of the chain
            
        Returns:
            The reasoning chain, or None if not found
        """
        return self.active_chains.get(chain_id)
        
    def execute_step(self, chain_id: str, step_result: Any) -> Dict:
        """
        Record the result of executing a step and advance the chain
        
        Args:
            chain_id: ID of the chain
            step_result: Result of executing the current step
            
        Returns:
            Updated chain context
        """
        chain = self.get_chain(chain_id)
        if not chain:
            return {"error": f"Chain not found: {chain_id}"}
            
        current_step = chain.get_current_step()
        if not current_step:
            return {"error": "No current step"}
            
        current_step.set_result(step_result)
        has_next = chain.advance()
        
        return {
            "chain_id": chain_id,
            "has_next_step": has_next,
            "context": chain.get_context()
        }
        
    def complete_chain(self, chain_id: str, final_response: str) -> Dict:
        """
        Complete a reasoning chain
        
        Args:
            chain_id: ID of the chain
            final_response: Final response to the user
            
        Returns:
            Result information
        """
        chain = self.get_chain(chain_id)
        if not chain:
            return {"error": f"Chain not found: {chain_id}"}
            
        chain.complete(final_response)
        
        return {
            "chain_id": chain_id,
            "is_completed": True,
            "final_response": final_response
        }
        
    def handle_request(self, chain_id: str, action: str, data: Dict) -> Dict:
        """
        Handle a request for a reasoning chain
        
        Args:
            chain_id: ID of the chain
            action: Action to perform
            data: Additional data for the action
            
        Returns:
            Result of the action
        """
        chain = self.get_chain(chain_id)
        if not chain and action != "create":
            return {"error": f"Chain not found: {chain_id}"}
            
        if action == "create":
            query = data.get("query")
            if not query:
                return {"error": "Query is required"}
            chain_id = self.create_chain(query)
            return {"chain_id": chain_id, "context": self.get_chain(chain_id).get_context()}
            
        elif action == "plan":
            # Add steps to the chain
            steps = data.get("steps", [])
            for step_data in steps:
                chain.add_step(
                    description=step_data["description"],
                    tool_name=step_data.get("tool_name"),
                    tool_args=step_data.get("tool_args")
                )
            return {"chain_id": chain_id, "context": chain.get_context()}
            
        elif action == "execute":
            step_result = data.get("result")
            return self.execute_step(chain_id, step_result)
            
        elif action == "complete":
            final_response = data.get("final_response")
            return self.complete_chain(chain_id, final_response)
            
        else:
            return {"error": f"Unknown action: {action}"}


# Initialize global instance
reasoning_engine = ReasoningEngine()