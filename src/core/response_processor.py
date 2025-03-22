import asyncio
import time
import json
import os
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
    
    print(f"🔄 Iniciando cadena de razonamiento: {chain.query}")
    print(f"🔄 Pasos planificados: {len(chain.steps)}")
    
    # Execute each step in order
    current_step_idx = 0
    while current_step_idx < len(chain.steps):
        step = chain.steps[current_step_idx]
        
        print(f"🔄 Ejecutando paso {current_step_idx + 1}/{len(chain.steps)}: {step.description}")
        
        try:
            # Execute the step
            result = await execute_reasoning_step(chain_id, step)
            
            # Print some debug info
            success = result.get("success", False)
            status = "✅ Éxito" if success else "❌ Error"
            print(f"{status} en paso {current_step_idx + 1}: {step.description}")
            
            if not success and "error" in result:
                print(f"Error: {result['error']}")
            
            # Update the step with the result
            step.set_result(result)
        except Exception as e:
            print(f"❌ Error ejecutando paso {current_step_idx + 1}: {str(e)}")
            # Create error result
            error_result = {
                "success": False,
                "error": str(e),
                "output": f"Error ejecutando paso: {str(e)}"
            }
            step.set_result(error_result)
        
        # Move to the next step
        current_step_idx += 1
        chain.current_step_idx = current_step_idx
    
    # Chain is complete
    chain.is_completed = True
    print(f"✅ Cadena de razonamiento completada")
    
    # Generate final response
    if not chain.final_response:
        # Get all step results
        steps_text = []
        for i, step in enumerate(chain.steps):
            if step.is_completed and step.result:
                output = step.result.get("output", "No output")
                # Truncate long outputs for clarity
                if len(output) > 200:
                    output = output[:200] + "..."
                steps_text.append(f"Paso {i+1}: {step.description}\nResultado: {output}")
        
        # Create a response using the results
        final_response = f"He completado tu solicitud: '{chain.query}'\n\n"
        
        # Check if all steps were successful
        all_success = all(step.result.get("success", False) for step in chain.steps if step.is_completed)
        
        if all_success:
            # Create a concise successful response
            if "buscar" in chain.query.lower() and "mover" in chain.query.lower():
                # For file operations, create a summary of what was done
                search_step = next((s for s in chain.steps if s.tool_name == "search_files"), None)
                move_step = next((s for s in chain.steps if "mover" in s.description.lower() or "mv" in str(s.tool_args)), None)
                
                if search_step and search_step.result:
                    files = search_step.result.get("files", [])
                    file_count = len(files)
                    if file_count > 0:
                        target_dir = None
                        if move_step and move_step.tool_args:
                            # Try to extract target directory from commands
                            if "commands" in move_step.tool_args:
                                for cmd in move_step.tool_args["commands"]:
                                    if "mkdir" in cmd:
                                        target_dir = cmd.split("mkdir")[1].strip().split()[-1].strip('"\'')
                                    elif "mv" in cmd and "-t" in cmd:
                                        target_dir = cmd.split("-t")[1].strip().split()[0].strip('"\'')
                        
                        if target_dir:
                            final_response = f"He organizado {file_count} archivos en la carpeta {target_dir}.\n\n"
                        else:
                            final_response = f"He encontrado y movido {file_count} archivos según tu solicitud.\n\n"
                            
                        # Add details of files
                        if file_count <= 5:
                            final_response += "Archivos procesados:\n"
                            for i, file in enumerate(files, 1):
                                name = file.get("name", "archivo desconocido")
                                final_response += f"{i}. {name}\n"
                        else:
                            final_response += f"Algunos de los archivos procesados: {files[0]['name']}, {files[1]['name']}, ..."
            else:
                # Generic success response
                final_response = f"He completado tu solicitud: '{chain.query}'"
        else:
            # Some steps failed
            failed_steps = [i+1 for i, step in enumerate(chain.steps) 
                          if step.is_completed and not step.result.get("success", False)]
            
            if failed_steps:
                final_response = f"No pude completar tu solicitud. Hubo problemas en los pasos {', '.join(map(str, failed_steps))}.\n\n"
                
                # Get the first error
                for step in chain.steps:
                    if step.is_completed and not step.result.get("success", False):
                        error = step.result.get("error", "Error desconocido")
                        final_response += f"Error: {error}"
                        break
        
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
    
    # Special command handlers
    if transcription.lower().startswith("create") or transcription.lower().startswith("make"):
        # Handle directory/file creation separately
        # Extract the directory/file to create
        words = transcription.lower().split()
        if "directory" in words or "folder" in words:
            # This is a directory creation request
            print("Detected directory creation request")
            # Try the direct approach with conversation API
            response = await run_conversation(transcription)
        else:
            # Use regular conversation for other creation requests
            response = await run_conversation(transcription)
            
    elif use_multi_step:
        # Force enable multi-step reasoning for file operations and search commands
        is_complex = False
        
        # Look for specific operation phrases and question words that might need multi-step processing
        file_op_indicators = ["search", "find", "organize", "move", "copy", "create folder", 
                           "sort", "rename", "delete", "remove", "list", "categorize", 
                           "what", "which", "where", "how many", "do i have"]
        
        for indicator in file_op_indicators:
            if indicator in transcription.lower():
                is_complex = True
                print(f"Detected complex operation: {indicator}")
                break
        
        # Check for specific file types and content
        file_types = ["files", "documents", "music", "photos", "images", "pdf", "mp3", "videos"]
        has_file_type = any(ft in transcription.lower() for ft in file_types)
        if has_file_type:
            print("Detected reference to file types")
            is_complex = True
        
        if is_complex:
            print("Using multi-step reasoning for complex task")
            
            try:
                # Get or create a reasoning chain
                chain_id = reasoning_engine.create_chain(transcription)
                
                # Run the conversation to generate the reasoning plan
                planning_response = await run_conversation(transcription)
                print(f"Planning response: {planning_response[:100]}...")
                
                # Check if planning was successful
                chain = reasoning_engine.get_chain(chain_id)
                if chain and chain.steps:
                    print(f"Chain has {len(chain.steps)} steps. Running reasoning chain...")
                    # Run the reasoning chain
                    response = await run_reasoning_chain(chain_id)
                    print(f"Reasoning chain completed successfully: {len(chain.steps)} steps")
                else:
                    # Fall back to regular conversation
                    print("No reasoning steps were generated, falling back to normal conversation")
                    response = await run_conversation(transcription)
            except Exception as e:
                print(f"Error in multi-step reasoning: {str(e)}")
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
    
    # Skip TTS for very long responses or if disabled in config
    use_tts = not config.get('NO_TTS', False) if config else True
    response_too_long = len(processed_response) > 500
    
    if use_tts and not response_too_long:
        try:
            # Convert text to speech and play audio
            audio_stream = await text_to_speech_stream(processed_response, config)
            await play_audio_stream(audio_stream)
        except Exception as e:
            print(f"Error en reproducción de audio: {str(e)}")
    elif response_too_long:
        print(f"Respuesta demasiado larga ({len(processed_response)} caracteres), omitiendo TTS")
    
    # Calculate total processing time
    total_time = time.time() - start_time
    print(f"Total processing time: {total_time:.2f} seconds")