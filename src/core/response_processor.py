import asyncio
import time
from src.audio.text_to_speech import text_to_speech_stream
from src.nlp.openai_response import run_conversation
from src.audio.audio_utils import play_audio_stream

async def process_and_play_response(transcription, speech_end_time, config=None):
    # Mark the start time for processing
    start_time = time.time()
    
    # Get AI response
    ai_response = await run_conversation(transcription)
    print(f"AI Response: {ai_response}")
    
    # Convert text to speech and play audio
    audio_stream = await text_to_speech_stream(ai_response, config)
    await play_audio_stream(audio_stream)
    
    # Calculate total processing time
    total_time = time.time() - start_time
    print(f"Total processing time: {total_time:.2f} seconds")