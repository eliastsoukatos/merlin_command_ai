import os
import json
from dotenv import load_dotenv
from openai import AsyncOpenAI
from src.commands.command_executor import execute_commands, execute_background_command
from src.utils.directory_manager import directory_manager

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize an empty conversation history
conversation_history = []

async def run_conversation(transcription):
    global conversation_history
    directory_info = directory_manager.get_all_directories()
    
    system_message = {"role": "system", "content": f"You are a virtual assistant that responds to questions and can execute terminal commands when necessary. You have access to the following directories:\n{directory_info}\nWhen referring to these directories in commands, use the full path."}
    
    # Add the new user message to the conversation history
    conversation_history.append({"role": "user", "content": transcription})
    
    # Prepare the messages for the API call
    messages = [system_message] + conversation_history

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

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            if tool_call.function.name == "execute_commands":
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