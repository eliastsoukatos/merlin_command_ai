# text_to_speech.py

import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

load_dotenv()

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Choose which service to use (set to False to use ElevenLabs)
USE_OPENAI = True

async def text_to_speech_stream(text):
    if USE_OPENAI:
        return await openai_tts_stream(text)
    else:
        return await elevenlabs_tts_stream(text)

async def openai_tts_stream(text):
    response = await openai_client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    return response.iter_bytes(chunk_size=4096)  # This returns a regular generator

# Code to use this function when switching to ElevenLabs
async def elevenlabs_tts_stream(text):
    eleven_labs_client = ElevenLabs(api_key=os.getenv('ELEVEN_LABS_API_KEY'))
    # Note: ElevenLabs doesn't have an async API, so we'll run it in a thread pool
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: eleven_labs_client.text_to_speech.convert_as_stream(
        voice_id="pMsXgVXv3BLzUgSXRplE",  # You can change this to your preferred voice
        optimize_streaming_latency="0",
        output_format="mp3_44100_128",
        text=text,
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.5,
        ),
    ))