# External libraries

# Suppress pydantic warnings
import warnings
warnings.filterwarnings("ignore", module="pydantic")

import asyncio
import argparse
import time
import pyaudio

# Internal files
from src.core.config import load_config
from src.audio.audio_utils import record_audio
from src.nlp.transcription import transcribe_audio
from src.wake_word.wake_word import initialize_wake_word_detection, detect_wake_word
from src.core.response_processor import process_and_play_response


# Simulate interaction

async def simulate_interaction(question, config):
    """
    Simulate an interaction with the voice assistant for testing purposes.
    
    Args:
    question (str): The simulated question
    config (dict): Configuration parameters
    
    Returns:
    None
    """
    print(f"Simulated question: {question}")
    speech_end_time = asyncio.get_event_loop().time()
    await process_and_play_response(question, speech_end_time, config)
    print("Simulation complete. Press 'w' to simulate wake word, or 'q' to quit.")


# Main software

async def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Voice Assistant")
    parser.add_argument("--simulate", action="store_true", help="Run in simulation mode")
    parser.add_argument("--use-wake-word", action="store_true", help="Run with wake word detection (requires Picovoice)")
    parser.add_argument("--multi-step", action="store_true", help="Enable multi-step reasoning for complex tasks")
    parser.add_argument("--no-tts", action="store_true", help="Disable text-to-speech output")
    args = parser.parse_args()

    # Load configuration from .env file
    config = load_config()
    
    # Add multi-step reasoning to config
    config['MULTI_STEP_REASONING'] = args.multi_step
    if args.multi_step:
        print("Multi-step reasoning enabled. Complex tasks will be processed in steps.")
        
    # Add no-tts option to config
    config['NO_TTS'] = args.no_tts
    if args.no_tts:
        print("Text-to-speech output disabled.")

    if args.simulate:
        # Simulation mode: use predefined questions instead of audio input
        print("Running in simulation mode. No audio input required.")
        print("Press 'w' to simulate wake word detection, or 'q' to quit.")
        
        while True:
            user_input = input().lower()
            if user_input == 'q':
                break
            elif user_input == 'w':
                print("Wake word detected!")
                for question in config['SAMPLE_QUESTIONS']:
                    await simulate_interaction(question, config)
                    user_input = input().lower()
                    if user_input == 'q':
                        return
                    elif user_input != 'w':
                        print("Waiting for wake word...")
                        break
            else:
                print("Waiting for wake word...")
        return
    
    if args.use_wake_word:
        # Initialize wake word detection and audio stream
        try:
            porcupine, cobra, audio_stream, pa = initialize_wake_word_detection(config)
        except Exception as e:
            print(f"Error initializing wake word detection: {e}")
            print("Falling back to manual text input mode.")
            # Fall back to manual mode if wake word detection fails
            args.use_wake_word = False
        
        if args.use_wake_word:  # Only enter this block if initialization succeeded
            print("Waiting for wake word...")

            try:
                while True:
                    # Continuously listen for the wake word
                    if await detect_wake_word(porcupine, audio_stream):
                        print("Wake word detected!")
                        
                        # Record audio after wake word detection
                        audio_file, speech_end_time = record_audio(audio_stream, pa, config, cobra)
                        
                        # Transcribe the recorded audio
                        transcription = transcribe_audio(audio_file, config)
                        print(f"Transcription: {transcription}")
                        
                        # Process the transcription and play the response
                        await process_and_play_response(transcription, speech_end_time, config)
                        
                        print("Waiting for wake word...")

            except KeyboardInterrupt:
                print("Stopping...")
            finally:
                # Clean up resources
                if audio_stream is not None:
                    audio_stream.close()
                if pa is not None:
                    pa.terminate()
                porcupine.delete()
                cobra.delete()
            
            return
    
    # Default mode: manual text input
    print("Running in manual text input mode.")
    print("Type your command or 'q' to quit.")
    
    try:
        while True:
            user_input = input("Enter command: ").strip()
            if user_input.lower() == 'q':
                break
            
            print(f"Processing: {user_input}")
            speech_end_time = asyncio.get_event_loop().time()
            # Process the input text directly
            await process_and_play_response(user_input, speech_end_time, config)
    
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        print("Exiting manual text input mode.")