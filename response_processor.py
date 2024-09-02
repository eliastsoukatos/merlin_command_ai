import asyncio
from text_to_speech import text_to_speech_stream
from openai_response import run_conversation
from audio_utils import play_audio_stream

async def process_and_play_response(transcription, speech_end_time):
    # Get AI response
    ai_response = await run_conversation(transcription)
    print(f"AI Response: {ai_response}")
    
    # Convert text to speech and play audio
    audio_stream = await text_to_speech_stream(ai_response)
    playback_start_time = await play_audio_stream(audio_stream)
    
    response_time = playback_start_time - speech_end_time
    print(f"Response time (from end of speech to start of playback): {response_time:.2f} seconds")