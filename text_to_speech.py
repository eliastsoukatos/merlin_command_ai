from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

async def text_to_speech_stream(text, config):
    """
    Convert text to speech using ElevenLabs API.
    """
    # Initialize the ElevenLabs client with the API key
    client = ElevenLabs(api_key=config['ELEVEN_LABS_API_KEY'])
    
    # Use ElevenLabs' text-to-speech API to convert text to speech
    audio_stream = client.text_to_speech.convert_as_stream(
        voice_id=config['VOICE_ID'],  # Use the specified voice ID
        optimize_streaming_latency=config['OPTIMIZE_STREAMING_LATENCY'],
        output_format="mp3_44100_128",  # Set the output audio format
        text=text,
        voice_settings=VoiceSettings(
            stability=config['VOICE_STABILITY'],
            similarity_boost=config['VOICE_SIMILARITY_BOOST'],
        ),
    )
    
    # Return the audio stream
    return audio_stream