import os
from dotenv import load_dotenv

def load_config():
    """
    Load configuration from environment variables.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Create a dictionary with all configuration parameters
    return {
        # API keys
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),  # Used for OpenAI API (transcription and AI response)
        'PICOVOICE_ACCESS_KEY': os.getenv('PICOVOICE_ACCESS_KEY'),  # Used for wake word detection
        'ELEVEN_LABS_API_KEY': os.getenv('ELEVEN_LABS_API_KEY'),  # Used for text-to-speech

        # AI model settings
        'GPT_MODEL': os.getenv('GPT_MODEL'),  # The GPT model to use for AI responses
        'SYSTEM_PROMPT': os.getenv('SYSTEM_PROMPT'),  # The system prompt for the AI model

        # Wake word settings
        'WAKE_WORD_PATH': os.getenv('WAKE_WORD_PATH'),  # Path to the wake word model file

        # Voice settings
        'VOICE_ID': os.getenv('VOICE_ID'),  # The voice ID to use for text-to-speech
        'OPTIMIZE_STREAMING_LATENCY': os.getenv('OPTIMIZE_STREAMING_LATENCY'),
        'VOICE_STABILITY': float(os.getenv('VOICE_STABILITY')),
        'VOICE_SIMILARITY_BOOST': float(os.getenv('VOICE_SIMILARITY_BOOST')),

        # Audio processing settings
        'VOICE_PROBABILITY_THRESHOLD': float(os.getenv('VOICE_PROBABILITY_THRESHOLD')),
        'SILENT_CHUNK_THRESHOLD': int(os.getenv('SILENT_CHUNK_THRESHOLD')),
        'MAX_RECORDING_TIME': int(os.getenv('MAX_RECORDING_TIME')),

        # Sample questions for simulation mode
        'SAMPLE_QUESTIONS': os.getenv('SAMPLE_QUESTIONS').split(','),

        # Audio configuration
        'CHUNK': 512,  # Number of frames per buffer
        'FORMAT': 8,  # 8 corresponds to pyaudio.paInt16
        'CHANNELS': 1,  # Mono audio
        'RATE': 16000,  # Sample rate (Hz)
    }