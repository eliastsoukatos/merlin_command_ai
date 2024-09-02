import os
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv


load_dotenv()

# Initialize Eleven Labs client
eleven_labs_client = ElevenLabs(api_key=os.getenv('ELEVEN_LABS_API_KEY'))

async def text_to_speech_stream(text):
    audio_stream = eleven_labs_client.text_to_speech.convert_as_stream(
        voice_id="pMsXgVXv3BLzUgSXRplE",  # You can change this to your preferred voice
        optimize_streaming_latency="0",
        output_format="mp3_44100_128",
        text=text,
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.5,
        ),
    )
    return audio_stream