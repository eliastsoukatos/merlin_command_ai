from openai import OpenAI

def transcribe_audio(file_path, config):
    """
    Transcribe an audio file using OpenAI's Whisper model.
    """
    # Initialize the OpenAI client with the API key
    client = OpenAI(api_key=config['OPENAI_API_KEY'])
    
    # Open the audio file in binary mode
    with open(file_path, "rb") as audio_file:
        # Use OpenAI's audio transcription API to convert speech to text
        transcription = client.audio.transcriptions.create(
            model="whisper-1",  # Use the Whisper model for transcription
            file=audio_file
        )
    
    # Return the transcribed text
    return transcription.text