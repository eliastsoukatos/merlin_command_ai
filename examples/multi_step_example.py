"""
Demonstration example for Merlin's multi-step reasoning system.
This example shows how the assistant breaks down complex tasks and executes them in steps.
"""

import os
import sys
import asyncio

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.nlp.openai_response import run_conversation, clear_conversation_history
from src.core.reasoning import reasoning_engine
from src.utils.directory_manager import directory_manager

async def demonstrate_multi_step_reasoning():
    """Run a demonstration of multi-step reasoning capabilities"""
    
    print("Merlin Multi-Step Reasoning Demonstration")
    print("----------------------------------------")
    
    # Set up a safe test directory
    test_dir = os.path.expanduser("~/merlin_test")
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    print(f"Created test directory: {test_dir}")
    
    # Add the test directory to the allowed directories
    directory_manager.add_directory(test_dir)
    print(f"Added {test_dir} to allowed directories")
    
    # Create some test files
    test_files = [
        "finance_report_2023.pdf",
        "finance_report_2024.pdf",
        "personal_budget.xlsx",
        "tax_info_2023.txt",
        "random_notes.txt",
        "holiday_photos.jpg"
    ]
    
    for file in test_files:
        file_path = os.path.join(test_dir, file)
        with open(file_path, "w") as f:
            f.write(f"This is a dummy file for {file}")
    
    print(f"Created {len(test_files)} test files in {test_dir}")
    
    # Create a complex task that requires multi-step reasoning
    complex_task = f"Find all files related to finance in {test_dir} and move them to a new folder called 'Finance'"
    
    print("\nStarting complex task:")
    print(f"Task: {complex_task}")
    print("\nProcessing...")
    
    # Run the conversation with the complex task
    response = await run_conversation(complex_task)
    
    print("\nTask complete!")
    print(f"Final response: {response}")
    
    # Print the reasoning chain if available
    active_chains = list(reasoning_engine.active_chains.values())
    if active_chains:
        chain = active_chains[0]
        print("\nReasoning Chain:")
        print(f"Query: {chain.query}")
        print(f"Steps: {len(chain.steps)}")
        
        for i, step in enumerate(chain.steps):
            print(f"\nStep {i+1}: {step.description}")
            if step.tool_name:
                print(f"Tool: {step.tool_name}")
                if step.tool_args:
                    print(f"Arguments: {step.tool_args}")
            if step.is_completed:
                print(f"Result: {step.result[:100]}..." if len(str(step.result)) > 100 else f"Result: {step.result}")
    
    # Clean up
    print("\nCleaning up...")
    for file in os.listdir(test_dir):
        os.remove(os.path.join(test_dir, file))
    
    # Remove the Finance directory if it was created
    finance_dir = os.path.join(test_dir, "Finance")
    if os.path.exists(finance_dir):
        for file in os.listdir(finance_dir):
            os.remove(os.path.join(finance_dir, file))
        os.rmdir(finance_dir)
    
    os.rmdir(test_dir)
    print(f"Removed test directory and all files")

if __name__ == "__main__":
    asyncio.run(demonstrate_multi_step_reasoning())