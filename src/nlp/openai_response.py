import os
import json
from dotenv import load_dotenv
from openai import AsyncOpenAI
from src.commands.command_executor import execute_commands, execute_background_command
from src.utils.directory_manager import directory_manager
from src.nlp.file_search import file_search_manager

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize an empty conversation history
conversation_history = []

async def run_conversation(transcription):
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
        }
    ]
    
    # In a production environment, we would add the file_search tool here
    # We're temporarily disabling it since we're using a mock implementation
    add_file_search = False
    vector_stores = file_search_manager.get_vector_stores()
    
    if add_file_search and vector_stores:
        # Get the first vector store for now
        # In the future, we could add logic to select the most relevant vector store
        vector_store = vector_stores[0]
        
        file_search_tool = {
            "type": "file_search",
            "vector_store_ids": [vector_store["id"]],
            "max_num_results": 5
        }
        
        tools.append(file_search_tool)

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    
    # Handle function calls
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            if tool_call.function and tool_call.function.name == "execute_commands":
                args = json.loads(tool_call.function.arguments)
                commands = args["commands"]
                background = args["background"]
                
                if background:
                    output = await execute_background_command(commands[0])
                else:
                    output = await execute_commands(commands)
                
                conversation_history.append({"role": "function", "name": "execute_commands", "content": output})
        
        final_response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages + [{"role": "function", "name": "execute_commands", "content": output}]
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