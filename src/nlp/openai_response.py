import os
import json
import uuid
from dotenv import load_dotenv
from openai import AsyncOpenAI
from src.commands.command_executor import execute_commands, execute_background_command
from src.utils.directory_manager import directory_manager
from src.nlp.file_search import file_search_manager
from src.core.reasoning import reasoning_engine

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize an empty conversation history
conversation_history = []

# Active reasoning chains
active_reasoning = {}

async def search_files(query, vector_store="default"):
    """Execute file search using the file search manager"""
    result = file_search_manager.search(query, vector_store)
    if "error" in result:
        return f"Error searching for files: {result['error']}"
    
    if "response" in result and hasattr(result["response"], "text"):
        return result["response"].text
    
    return "No results found."

async def run_reasoning_chain(query):
    """
    Start a new reasoning chain for complex tasks
    
    Args:
        query: User's request
        
    Returns:
        Assistant's response with reasoning
    """
    global conversation_history
    
    # Get system context
    directory_info = directory_manager.get_all_directories()
    indexed_dirs = file_search_manager.get_indexed_directories()
    indexed_dirs_info = ""
    if indexed_dirs:
        indexed_dirs_info = "You have access to the following indexed directories for file search:\n"
        for i, dir_path in enumerate(indexed_dirs, 1):
            indexed_dirs_info += f"{i}. {dir_path}\n"
    
    # Create reasoning system prompt
    system_message = {"role": "system", "content": f"""You are a virtual assistant with multi-step reasoning capabilities. You can break down complex tasks into logical steps and execute them in sequence.

You have access to the following directories:
{directory_info}

{indexed_dirs_info}

## Instructions for Multi-step Reasoning:
1. Analyze the user's request to determine if it requires multiple steps
2. For complex tasks, break them down into sequential steps
3. Execute each step using the appropriate tool
4. Use results from previous steps to inform subsequent steps
5. Synthesize a final response that addresses the user's request

## Available Tools:
1. execute_commands: Run terminal commands (use full paths from accessible directories)
2. search_files: Search for files in indexed directories
3. plan_reasoning: Create a step-by-step plan for complex tasks

When you need to execute multiple steps where the output of one step feeds into another, use the planning capability.
"""}
    
    # Start the planning process
    planning_messages = [
        system_message,
        {"role": "user", "content": f"I need to break down this task into logical steps: '{query}'\nCreate a step-by-step plan to accomplish this."}
    ]
    
    planning_response = await client.chat.completions.create(
        model="gpt-4o",
        messages=planning_messages,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "plan_reasoning",
                    "description": "Create a step-by-step reasoning plan",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "steps": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "description": {
                                            "type": "string",
                                            "description": "Description of the step"
                                        },
                                        "tool_name": {
                                            "type": "string",
                                            "enum": ["execute_commands", "search_files", "synthesize"],
                                            "description": "Tool to use for this step (or 'synthesize' for reasoning)"
                                        },
                                        "tool_args": {
                                            "type": "object",
                                            "description": "Arguments for the tool"
                                        }
                                    },
                                    "required": ["description"]
                                }
                            }
                        },
                        "required": ["steps"]
                    }
                }
            }
        ],
        tool_choice="auto"
    )
    
    response_message = planning_response.choices[0].message
    
    # Create a new reasoning chain
    chain_id = reasoning_engine.create_chain(query)
    
    # Extract the planning steps
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            if tool_call.function and tool_call.function.name == "plan_reasoning":
                plan = json.loads(tool_call.function.arguments)
                
                # Add steps to reasoning chain
                reasoning_engine.handle_request(chain_id, "plan", plan)
                
                # Start executing the plan (first step)
                chain = reasoning_engine.get_chain(chain_id)
                current_step = chain.get_current_step()
                
                # Execute the first step
                step_result = await execute_reasoning_step(chain_id, current_step)
                
                # Return initial response to user
                return f"I'll help you with your request: '{query}'\n\nI've broken this down into {len(chain.steps)} steps. Working on step 1: {current_step.description}"
    
    # Fallback if planning fails
    return await run_conversation(query)

async def execute_reasoning_step(chain_id, step):
    """
    Execute a step in a reasoning chain
    
    Args:
        chain_id: ID of the reasoning chain
        step: The reasoning step to execute
        
    Returns:
        Result of the step execution
    """
    result = None
    
    if step.tool_name == "execute_commands":
        commands = step.tool_args.get("commands", [])
        background = step.tool_args.get("background", False)
        
        if background and commands:
            result = await execute_background_command(commands[0])
        elif commands:
            result = await execute_commands(commands)
        else:
            result = "No commands specified."
            
    elif step.tool_name == "search_files":
        query = step.tool_args.get("query", "")
        vector_store = step.tool_args.get("vector_store", "default")
        
        if query:
            result = await search_files(query, vector_store)
        else:
            result = "No search query specified."
            
    elif step.tool_name == "synthesize" or not step.tool_name:
        # This is a reasoning step without a specific tool
        system_message = {"role": "system", "content": "You are an assistant helping with a multi-step reasoning process. Analyze the information provided and generate insights."}
        
        # Get previous steps and their results
        chain = reasoning_engine.get_chain(chain_id)
        prev_steps = []
        for i in range(step.step_id):
            prev_step = chain.steps[i]
            if prev_step.is_completed:
                prev_steps.append(f"Step {i+1}: {prev_step.description}\nResult: {prev_step.result}")
        
        prev_steps_text = "\n\n".join(prev_steps)
        
        user_message = f"Based on the previous steps:\n\n{prev_steps_text}\n\nComplete the following reasoning step: {step.description}"
        
        messages = [
            system_message,
            {"role": "user", "content": user_message}
        ]
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        
        result = response.choices[0].message.content
    
    # Record result and advance chain
    execution_result = reasoning_engine.execute_step(chain_id, result)
    
    # Check if there's another step to execute
    if execution_result.get("has_next_step", False):
        chain = reasoning_engine.get_chain(chain_id)
        next_step = chain.get_current_step()
        
        # Execute the next step
        await execute_reasoning_step(chain_id, next_step)
    else:
        # Complete the chain with a final response
        await complete_reasoning_chain(chain_id)
    
    return result

async def complete_reasoning_chain(chain_id):
    """
    Complete a reasoning chain with a final response
    
    Args:
        chain_id: ID of the reasoning chain
        
    Returns:
        Final response
    """
    chain = reasoning_engine.get_chain(chain_id)
    
    if not chain:
        return "Error: Reasoning chain not found."
    
    # Get all steps and their results
    steps_info = []
    for i, step in enumerate(chain.steps):
        if step.is_completed:
            steps_info.append(f"Step {i+1}: {step.description}\nResult: {step.result}")
    
    steps_text = "\n\n".join(steps_info)
    
    # Generate final response
    system_message = {"role": "system", "content": "You are an assistant completing a multi-step reasoning task. Synthesize the results of all steps into a coherent final response that directly answers the user's original query."}
    
    user_message = f"Original query: {chain.query}\n\nSteps and results:\n\n{steps_text}\n\nProvide a clear, concise final response that addresses the original query based on these results."
    
    messages = [
        system_message,
        {"role": "user", "content": user_message}
    ]
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    
    final_response = response.choices[0].message.content
    
    # Complete the chain
    reasoning_engine.complete_chain(chain_id, final_response)
    
    return final_response

async def run_conversation(transcription):
    """
    Run a regular conversation without multi-step reasoning
    
    Args:
        transcription: User's message
        
    Returns:
        Assistant's response
    """
    global conversation_history
    directory_info = directory_manager.get_all_directories()
    
    # Get indexed directories information
    indexed_dirs = file_search_manager.get_indexed_directories()
    indexed_dirs_info = ""
    if indexed_dirs:
        indexed_dirs_info = "You have access to the following indexed directories for file search:\n"
        for i, dir_path in enumerate(indexed_dirs, 1):
            indexed_dirs_info += f"{i}. {dir_path}\n"
    
    system_message = {"role": "system", "content": f"""You are a virtual assistant that responds to questions and can execute terminal commands when necessary. 

You have access to the following directories:
{directory_info}

{indexed_dirs_info}

When referring to these directories in commands, use the full path.
When searching for files or information within indexed directories, use the file_search tool.
"""}
    
    # Add the new user message to the conversation history
    conversation_history.append({"role": "user", "content": transcription})
    
    # Prepare the messages for the API call
    messages = [system_message] + conversation_history
    
    # Check if this request might need multi-step reasoning
    complexity_check = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You determine if a user request requires multi-step reasoning. Respond with either 'SIMPLE' or 'COMPLEX'."},
            {"role": "user", "content": f"Does this request require multiple steps to complete? '{transcription}'"}
        ],
        max_tokens=10
    )
    
    complexity_response = complexity_check.choices[0].message.content.strip().upper()
    
    # For complex requests, use the reasoning engine
    if "COMPLEX" in complexity_response and "STEP" in complexity_response:
        return await run_reasoning_chain(transcription)
    
    # For simple requests, use the regular conversation flow
    # Build tools array
    tools = [
        {
            "type": "function",
            "function": {
                "name": "execute_commands",
                "description": "Executes terminal commands based on the user input",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "commands": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of terminal commands to execute"
                        },
                        "background": {
                            "type": "boolean",
                            "description": "Whether to run the command in the background"
                        }
                    },
                    "required": ["commands", "background"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_files",
                "description": "Search for files in indexed directories",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "vector_store": {
                            "type": "string",
                            "description": "Name of the vector store to search in (default: 'default')"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    
    # Handle function calls
    if response_message.tool_calls:
        # Add the assistant's message with the tool calls
        conversation_history.append({"role": "assistant", "content": None, "tool_calls": response_message.tool_calls})
        
        # Process each tool call
        for tool_call in response_message.tool_calls:
            if tool_call.function:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "execute_commands":
                    commands = function_args["commands"]
                    background = function_args["background"]
                    
                    if background:
                        output = await execute_background_command(commands[0])
                    else:
                        output = await execute_commands(commands)
                    
                    conversation_history.append({"role": "tool", "tool_call_id": tool_call.id, "name": function_name, "content": output})
                
                elif function_name == "search_files":
                    query = function_args["query"]
                    vector_store = function_args.get("vector_store", "default")
                    
                    output = await search_files(query, vector_store)
                    conversation_history.append({"role": "tool", "tool_call_id": tool_call.id, "name": function_name, "content": output})
        
        # Get the final response
        final_response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages + conversation_history[-2:]  # Add the tool call and tool response
        )
        assistant_response = final_response.choices[0].message.content
    else:
        # For regular responses
        assistant_response = response_message.content

    # Add the assistant's response to the conversation history
    conversation_history.append({"role": "assistant", "content": assistant_response})
    
    # Trim the conversation history if it gets too long
    if len(conversation_history) > 10:  # Keep last 10 messages
        conversation_history = conversation_history[-10:]

    return assistant_response

# Function to clear conversation history
def clear_conversation_history():
    global conversation_history
    conversation_history = []