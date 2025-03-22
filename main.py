# Entry point for Merlin Voice Assistant
# This file serves as the main entry point for the application

import asyncio
from src.core.main import main

if __name__ == "__main__":
    asyncio.run(main())