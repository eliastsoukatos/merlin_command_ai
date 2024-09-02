# External libraries

import asyncio
import argparse
import time

# Internal files

from config import load_config
from audio_utils import record_audio
from transcription import transcribe_audio
from wake_word import initialize_wake_word_detection, detect_wake_word
from response_processor import process_and_play_response


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
    args = parser.parse_args()

    # Load configuration from .env file
    config = load_config()

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

    # Initialize wake word detection and audio stream
    porcupine, cobra, audio_stream, pa = initialize_wake_word_detection(config)

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
                await process_and_play_response(transcription, speech_end_time)
                
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

if __name__ == "__main__":
    asyncio.run(main())