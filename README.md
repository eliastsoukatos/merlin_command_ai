# Merlin - Voice-Activated AI Assistant

Merlin is a powerful, voice-activated AI assistant that can interact with users through speech or text input, process natural language commands, and execute various tasks on your system.

## Features

- **Voice Activation**: Wake Merlin by saying "Merlin" and then speak your command
- **Natural Language Processing**: Understand and process natural language commands using OpenAI's GPT models
- **Text-to-Speech**: Convert AI responses to speech using OpenAI or ElevenLabs TTS
- **File Operations**: Search for files and execute file operations in approved directories
- **Multi-Step Reasoning**: Break down complex tasks into logical steps and execute them sequentially
- **Command Execution**: Run system commands with security controls to prevent dangerous operations
- **Flexible Modes**: Choose between wake word detection, manual text input, or simulation mode

## Installation

### Prerequisites

- Python 3.9+
- [Picovoice](https://picovoice.ai/) Access Key (for wake word detection)
- OpenAI API Key
- ElevenLabs API Key (optional, for enhanced text-to-speech)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/merlin_command_ai.git
   cd merlin_command_ai
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your API keys (see `example.env`):
   ```bash
   cp example.env .env
   # Edit the .env file with your own API keys and settings
   ```

## Usage

### Basic Usage

Run Merlin in manual text input mode:
```bash
python main.py
```

### With Wake Word Detection

To enable wake word detection, run:
```bash
python main.py --use-wake-word
```

When the program starts, it will listen for the wake word "Merlin". When detected, it will start recording your command until you stop speaking. Merlin will then process your command and respond.

### With Multi-Step Reasoning

For complex tasks that require breaking down into sequential steps:
```bash
python main.py --multi-step
```

This enables Merlin to:
1. Break down complex requests into logical steps
2. Execute each step sequentially
3. Use results from previous steps to inform subsequent steps
4. Synthesize a final response addressing your original request

### Without Text-to-Speech

If you prefer text responses rather than spoken ones:
```bash
python main.py --no-tts
```

### Simulation Mode

For testing with predefined questions:
```bash
python main.py --simulate
```

## Configuration

The application's behavior is controlled through environment variables in the `.env` file. Key settings include:

- API keys for OpenAI, Picovoice, and ElevenLabs
- AI model configurations
- Voice settings
- Audio processing parameters
- Sample questions for simulation mode

See the `example.env` file for all available configuration options.

## Directory Structure

```
merlin_command_ai/
├── docs/                  # Documentation
├── examples/              # Example scripts
├── src/                   # Source code
│   ├── audio/             # Audio input/output utilities
│   ├── commands/          # Command execution modules  
│   ├── core/              # Core functionality
│   ├── nlp/               # Natural language processing modules
│   ├── utils/             # Utility functions
│   └── wake_word/         # Wake word detection
├── main.py                # Entry point
├── merlin_files.py        # File management utilities
├── Merlin_en_linux_v3_0_0.ppn  # Wake word model file
└── requirements.txt       # Dependencies
```

## Examples

### Simple Command

```
You: "What's the weather like today?"
Merlin: "I can't directly access real-time data like weather, but I can help you find out. Would you like me to open a weather website for you or explain how to check the weather using other tools?"
```

### File Operations

```
You: "Find all PDF files in my Documents folder"
Merlin: "I found 5 PDF files in your Documents folder:
- report.pdf
- invoice_2023.pdf
- user_manual.pdf
- contract.pdf
- notes.pdf"
```

### Multi-Step Task

```
You: "Find all Python files that import pandas and create a backup of them"
Merlin: "I'll help with that. First, let me search for Python files that import pandas..."
[Merlin works through multiple steps]
"I've completed your request. I found 3 Python files that import pandas and created backups with .bak extension:
- data_analysis.py → data_analysis.py.bak
- visualization.py → visualization.py.bak
- import_module.py → import_module.py.bak"
```

## Extending Merlin

### Adding New Commands

You can extend Merlin's functionality by adding new command handlers in the `src/commands/` directory.

### Custom Wake Word

To use a custom wake word, you'll need to create a new wake word model using Picovoice's Porcupine service and update the `WAKE_WORD_PATH` in your `.env` file.

## Troubleshooting

### Audio Issues

If you encounter audio input/output issues:
- Ensure your microphone and speakers are properly connected and functional
- Check that PyAudio is correctly installed
- Adjust the audio settings in the `.env` file

### Wake Word Detection

If wake word detection isn't working:
- Verify your Picovoice Access Key is correct
- Ensure the wake word model file path is correct
- Check that the correct audio hardware is being used

## License

This project is licensed under the terms of the license included in the `LICENSE.txt` file.

## Acknowledgments

- [OpenAI](https://openai.com/) for GPT models and TTS
- [Picovoice](https://picovoice.ai/) for wake word detection
- [ElevenLabs](https://elevenlabs.io/) for realistic voice synthesis