import asyncio
import subprocess

async def execute_command(command):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if stdout:
        return stdout.decode()
    elif stderr:
        return f"Error: {stderr.decode()}"
    else:
        return "Command executed successfully, but there was no output."

async def execute_commands(commands):
    tasks = [execute_command(cmd) for cmd in commands]
    results = await asyncio.gather(*tasks)
    return "\n".join(results)

async def execute_background_command(command):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
        start_new_session=True
    )
    return f"Command '{command}' started in the background."