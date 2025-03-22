import asyncio
import subprocess
import os
import re
import shlex
from typing import List, Dict, Optional, Any, Tuple, Union
from src.core.reasoning import ReasoningStep

# List of potentially dangerous command patterns
DANGEROUS_PATTERNS = [
    r"rm\s+(-[rf]+\s+)?/",            # rm commands targeting root
    r"sudo",                          # sudo commands
    r"chmod\s+777",                   # overly permissive chmod
    r"mkfs",                          # format drives
    r">(>)?.*/(passwd|shadow|group)", # write to system files
    r"dd\s+.*\s+of=/dev/",            # write directly to devices
    r":(){:|:&};:",                   # fork bomb
]

# List of safe command categories
SAFE_COMMAND_CATEGORIES = {
    "file_operations": ["ls", "cp", "mv", "mkdir", "touch", "cat", "head", "tail", "find", "grep"],
    "navigation": ["cd", "pwd"],
    "information": ["file", "stat", "du", "df", "wc"],
    "archives": ["tar", "zip", "unzip", "gzip", "gunzip"],
    "net_tools": ["ping", "wget", "curl"]
}

class CommandVerifier:
    """
    Verifies the safety of commands before execution
    """
    
    @staticmethod
    def is_dangerous(command: str) -> Tuple[bool, str]:
        """
        Check if a command contains dangerous patterns
        
        Args:
            command: The command to check
            
        Returns:
            Tuple of (is_dangerous, reason)
        """
        # Logging for debugging
        print(f"Verificando comando: {command}")
        
        # Check against dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command):
                print(f"⚠️ Comando peligroso (patrón {pattern}): {command}")
                return True, f"Command matches dangerous pattern: {pattern}"
        
        # Get the base command (first word)
        base_command = command.strip().split()[0] if command.strip() else ""
        
        # Special case for mkdir and mv which are essential for our file operations
        if base_command in ["mkdir", "mv", "cp"]:
            # These are essential commands that we need to allow
            print(f"✅ Comando permitido (esencial): {command}")
            return False, ""
        
        # Check if it's in our list of safe commands
        is_in_safe_list = False
        for category, commands in SAFE_COMMAND_CATEGORIES.items():
            if base_command in commands:
                is_in_safe_list = True
                break
        
        if not is_in_safe_list and base_command not in ["echo", "printf"]:
            print(f"⚠️ Comando no en lista permitida: {base_command}")
            return True, f"Command '{base_command}' is not in the allowed command list"
        
        # Additional specific checks
        if ">" in command and ("/etc/" in command or "/var/" in command):
            print(f"⚠️ Comando intenta escribir a directorios del sistema: {command}")
            return True, "Command attempts to write to system directories"
        
        if "|" in command and any(cmd in command for cmd in ["nohup", "daemon", "&", "disown"]):
            print(f"⚠️ Comando intenta ejecución en segundo plano con pipes: {command}")
            return True, "Command attempts to background execution with pipes"
        
        print(f"✅ Comando verificado y permitido: {command}")    
        return False, ""
    
    @staticmethod
    def verify_command_with_context(command: str, context: Dict) -> Tuple[bool, str]:
        """
        Verify a command with additional context information
        
        Args:
            command: The command to verify
            context: Contextual information
            
        Returns:
            Tuple of (is_safe, reason)
        """
        # First apply basic safety checks
        is_dangerous, reason = CommandVerifier.is_dangerous(command)
        if is_dangerous:
            return False, reason
        
        # Check if file operations target only approved directories
        if any(cmd in command.split() for cmd in ["cp", "mv", "rm", "mkdir", "touch"]):
            # Get approved directories from context
            approved_dirs = context.get("approved_directories", [])
            
            # Debug info
            print(f"Directorios aprobados: {approved_dirs}")
            
            # Consider the user's home directory as approved
            home_dir = os.path.expanduser("~")
            if home_dir not in approved_dirs:
                approved_dirs.append(home_dir)
                print(f"Añadido directorio home: {home_dir}")
            
            # Extract paths from the command
            try:
                words = shlex.split(command)
                paths = [w for w in words[1:] if not w.startswith("-") and "/" in w]
                
                print(f"Paths extraídos del comando: {paths}")
                
                # Check if all paths are within approved directories
                for path in paths:
                    if not path.startswith("/"):
                        # Convert relative path to absolute
                        abs_path = os.path.abspath(path)
                        print(f"Convertido path relativo: {path} -> {abs_path}")
                        path = abs_path
                        
                    is_approved = False
                    for approved_dir in approved_dirs:
                        if path == approved_dir or path.startswith(approved_dir + "/"):
                            is_approved = True
                            print(f"✅ Path aprobado: {path} (en {approved_dir})")
                            break
                    
                    if not is_approved:
                        print(f"⚠️ Path no aprobado: {path}")
                        return False, f"Command targets unapproved directory: {path}"
            except Exception as e:
                print(f"⚠️ Error al analizar rutas en comando: {str(e)}")
                # Be permissive in case of parsing errors, since we've already passed basic safety checks
                pass
        
        return True, ""

class CommandExecutor:
    """
    Enhanced command executor with context awareness and safety checks
    """
    
    def __init__(self):
        """Initialize the command executor"""
        self.verifier = CommandVerifier()
        self.command_history = []
        self.unsafe_attempt_count = 0
    
    async def execute_command(self, command: str, context: Optional[Dict] = None) -> Dict:
        """
        Execute a shell command with safety verification
        
        Args:
            command: The command to execute
            context: Optional execution context
            
        Returns:
            Dictionary with execution results
        """
        result = {
            "success": False,
            "output": "",
            "command": command,
            "error": None
        }
        
        # Verify command safety
        context = context or {}
        is_safe, reason = self.verifier.verify_command_with_context(command, context)
        
        if not is_safe:
            self.unsafe_attempt_count += 1
            result["error"] = f"Unsafe command rejected: {reason}"
            return result
        
        # Add to history
        self.command_history.append(command)
        
        try:
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            # Process result
            if stdout:
                result["output"] = stdout.decode()
                result["success"] = True
            elif stderr:
                result["output"] = f"Error: {stderr.decode()}"
                result["error"] = stderr.decode()
            else:
                result["output"] = "Command executed successfully, but there was no output."
                result["success"] = True
                
            # Add return code
            result["return_code"] = process.returncode
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            result["output"] = f"Error executing command: {str(e)}"
            return result
    
    async def execute_commands(self, commands: List[str], context: Optional[Dict] = None) -> Dict:
        """
        Execute multiple commands
        
        Args:
            commands: List of commands to execute
            context: Optional execution context
            
        Returns:
            Dictionary with combined execution results
        """
        results = []
        all_success = True
        combined_output = ""
        
        for cmd in commands:
            result = await self.execute_command(cmd, context)
            results.append(result)
            
            if not result["success"]:
                all_success = False
            
            combined_output += f"Command: {cmd}\n{result['output']}\n\n"
        
        return {
            "success": all_success,
            "output": combined_output.strip(),
            "commands": commands,
            "individual_results": results
        }
    
    async def execute_background_command(self, command: str, context: Optional[Dict] = None) -> Dict:
        """
        Execute a command in the background
        
        Args:
            command: The command to execute
            context: Optional execution context
            
        Returns:
            Dictionary with execution status
        """
        result = {
            "success": False,
            "output": "",
            "command": command,
            "error": None
        }
        
        # Verify command safety
        context = context or {}
        is_safe, reason = self.verifier.verify_command_with_context(command, context)
        
        if not is_safe:
            self.unsafe_attempt_count += 1
            result["error"] = f"Unsafe command rejected: {reason}"
            return result
        
        # Add to history
        self.command_history.append(f"[background] {command}")
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                start_new_session=True
            )
            
            result["output"] = f"Command '{command}' started in the background."
            result["success"] = True
            return result
            
        except Exception as e:
            result["error"] = str(e)
            result["output"] = f"Error starting background command: {str(e)}"
            return result
    
    def generate_command(self, action: str, files: List[Dict], target_dir: str) -> str:
        """
        Generate a command based on an action and file list
        
        Args:
            action: The action to perform (e.g., "move", "copy", "delete")
            files: List of files to operate on
            target_dir: Target directory for operations
            
        Returns:
            Generated command string
        """
        if not files:
            return ""
            
        file_paths = [f'"{file["path"]}"' for file in files]
        file_paths_str = " ".join(file_paths)
        
        if action == "move":
            return f'mkdir -p "{target_dir}" && mv {file_paths_str} "{target_dir}"'
        elif action == "copy":
            return f'mkdir -p "{target_dir}" && cp {file_paths_str} "{target_dir}"'
        elif action == "delete":
            return f'rm {file_paths_str}'
        else:
            return ""
    
    async def execute_step(self, step: ReasoningStep, context: Dict) -> Dict:
        """
        Execute a command step in a reasoning chain
        
        Args:
            step: The reasoning step
            context: Current context
            
        Returns:
            Execution results
        """
        step_args = step.tool_args
        action = step_args.get("action", "")
        commands = step_args.get("commands", [])
        
        # If we have explicit commands, execute them
        if commands:
            if len(commands) == 1 and step_args.get("background", False):
                return await self.execute_background_command(commands[0], context)
            else:
                return await self.execute_commands(commands, context)
        
        # If we need to generate commands based on files
        if action and "files" in step_args and "target_dir" in step_args:
            files = step_args["files"]
            target_dir = step_args["target_dir"]
            
            command = self.generate_command(action, files, target_dir)
            if command:
                return await self.execute_command(command, context)
        
        return {
            "success": False,
            "output": "Invalid command step: missing required parameters",
            "error": "Missing required parameters"
        }

# Initialize global instance
command_executor = CommandExecutor()

# Legacy functions for backward compatibility
async def execute_command(command):
    result = await command_executor.execute_command(command)
    return result["output"]

async def execute_commands(commands):
    result = await command_executor.execute_commands(commands)
    return result["output"]

async def execute_background_command(command):
    result = await command_executor.execute_background_command(command)
    return result["output"]