import asyncio
import time
import json
from typing import Dict, List, Optional, Any, Tuple, Union

from src.audio.text_to_speech import text_to_speech_stream
from src.nlp.openai_response import run_conversation
from src.audio.audio_utils import play_audio_stream
from src.core.reasoning import reasoning_engine, ReasoningStep
from src.core.context_manager import context_manager
from src.nlp.file_search import file_search_manager
from src.commands.command_executor import command_executor

def process_response(response):
    """Process the response from the AI model
    
    Args:
        response (str): The raw response from the AI model
        
    Returns:
        str: The processed response
    """
    # Remove any potential function calling artifacts
    if "```" in response:
        # Extract code blocks and clean up
        parts = response.split("```")
        cleaned_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 0:  # This is text outside code blocks
                cleaned_parts.append(part)
        response = "".join(cleaned_parts)
    
    # Format the response for better readability
    response = response.strip()
    
    return response

async def execute_reasoning_step(chain_id: str, step: ReasoningStep) -> Dict:
    """
    Execute a step in the reasoning process
    
    Args:
        chain_id: ID of the reasoning chain
        step: The step to execute
        
    Returns:
        Result of the step execution
    """
    # Get the context for this step
    step_context = context_manager.get_step_context(chain_id, step.step_id)
    
    # Execute the step based on its tool
    result = {}
    
    if step.tool_name == "execute_commands":
        # Execute command(s)
        result = await command_executor.execute_step(step, step_context)
    elif step.tool_name == "search_files":
        # Execute file search
        result = file_search_manager.execute_search_step(step)
    elif step.tool_name == "synthesize" or not step.tool_name:
        # This is a reasoning step that doesn't use a tool
        result = {
            "success": True,
            "output": "This step was a reasoning/synthesis step with no tool execution required.",
            "type": "reasoning"
        }
    else:
        # Unknown tool
        result = {
            "success": False,
            "error": f"Unknown tool: {step.tool_name}",
            "output": f"Could not execute step with unknown tool: {step.tool_name}"
        }
    
    # Update the context with the result
    context_manager.update_context_from_step_result(
        chain_id, 
        result, 
        {"step_id": step.step_id, "tool_name": step.tool_name}
    )
    
    return result

async def run_reasoning_chain(chain_id: str) -> str:
    """
    Run a reasoning chain from start to finish
    
    Args:
        chain_id: ID of the reasoning chain
        
    Returns:
        Final response from the chain
    """
    chain = reasoning_engine.get_chain(chain_id)
    if not chain:
        return "Error: Reasoning chain not found."
    
    # Execute each step in order
    current_step_idx = 0
    while current_step_idx < len(chain.steps):
        step = chain.steps[current_step_idx]
        
        # Execute the step
        result = await execute_reasoning_step(chain_id, step)
        
        # Update the step with the result
        step.set_result(result)
        
        # Move to the next step
        current_step_idx += 1
        chain.current_step_idx = current_step_idx
    
    # Chain is complete
    chain.is_completed = True
    
    # Generate final response
    if not chain.final_response:
        # Get all step results
        steps_text = []
        for i, step in enumerate(chain.steps):
            if step.is_completed and step.result:
                output = step.result.get("output", "No output")
                steps_text.append(f"Step {i+1}: {step.description}\nResult: {output}")
        
        # Create a response using the results
        final_response = f"Task completed: {chain.query}\n\n"
        final_response += "Summary of steps:\n"
        for i, step in enumerate(chain.steps):
            final_response += f"- Step {i+1}: {step.description}\n"
        
        # Set as the chain's final response
        chain.final_response = final_response
    
    return chain.final_response

async def process_and_play_response(transcription, speech_end_time, config=None):
    """Process the transcription, get AI response, and play audio
    
    Args:
        transcription (str): User's transcribed speech or text input
        speech_end_time (float): Time when the speech ended
        config (dict, optional): Configuration parameters
        
    Returns:
        None
    """
    # Mark the start time for processing
    start_time = time.time()
    
    print("Processing your request...")
    
    # Get AI response with or without multi-step reasoning
    use_multi_step = config.get('MULTI_STEP_REASONING', False) if config else False
    response = None
    
    if use_multi_step:
        # Check if this is a complex query that would benefit from multi-step reasoning
        complexity_threshold = 0.6  # Configurable threshold
        
        # Look for complex task indicators in the query
        complex_indicators = [
            "find", "search", "organize", "move", "copy", "sort", "create",
            "analyze", "compare", "extract", "convert", "transform"
        ]
        
        # Simple complexity heuristic
        words = transcription.lower().split()
        indicator_count = sum(1 for word in words if word in complex_indicators)
        complexity_score = indicator_count / max(len(words), 1)
        
        is_complex = complexity_score >= complexity_threshold
        
        if is_complex:
            print("Using multi-step reasoning for complex task")
            
            # Get or create a reasoning chain
            chain_id = reasoning_engine.create_chain(transcription)
            
            # Run the conversation to generate the reasoning plan
            await run_conversation(transcription)
            
            # Check if planning was successful
            chain = reasoning_engine.get_chain(chain_id)
            if chain and chain.steps:
                # Run the reasoning chain
                response = await run_reasoning_chain(chain_id)
            else:
                # Fall back to regular conversation
                response = await run_conversation(transcription)
        else:
            # Use regular conversation for simple queries
            response = await run_conversation(transcription)
    else:
        # Use regular conversation mode
        response = await run_conversation(transcription)
    
    # Process the response
    processed_response = process_response(response)
    print(f"AI Response: {processed_response}")
    
    # Convert text to speech and play audio
    audio_stream = await text_to_speech_stream(processed_response, config)
    await play_audio_stream(audio_stream)
    
    # Calculate total processing time
    total_time = time.time() - start_time
    print(f"Total processing time: {total_time:.2f} seconds")