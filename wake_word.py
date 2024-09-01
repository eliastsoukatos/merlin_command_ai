import pyaudio
import pvporcupine
import pvcobra
import struct

def initialize_wake_word_detection(config):
    """
    Initialize wake word detection components.
    """
    # Initialize Porcupine for wake word detection
    porcupine = pvporcupine.create(
        access_key=config['PICOVOICE_ACCESS_KEY'],
        keyword_paths=[config['WAKE_WORD_PATH']]
    )

    # Initialize Cobra for voice activity detection
    cobra = pvcobra.create(access_key=config['PICOVOICE_ACCESS_KEY'])

    # Initialize PyAudio for audio input
    pa = pyaudio.PyAudio()
    audio_stream = pa.open(
        rate=config['RATE'],
        channels=config['CHANNELS'],
        format=config['FORMAT'],
        input=True,
        frames_per_buffer=config['CHUNK']
    )

    return porcupine, cobra, audio_stream, pa

async def detect_wake_word(porcupine, audio_stream):
    """
    Detect wake word in the audio stream.
    """
    # Read a frame of audio from the stream
    pcm = audio_stream.read(porcupine.frame_length)
    
    # Convert the audio data to the format expected by Porcupine
    pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

    # Process the audio frame with Porcupine to detect the wake word
    keyword_index = porcupine.process(pcm)

    # Return True if the wake word is detected (keyword_index >= 0), False otherwise
    return keyword_index >= 0