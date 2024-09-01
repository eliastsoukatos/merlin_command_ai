import time
import wave
import struct
import sounddevice as sd
import numpy as np
from pydub import AudioSegment
import io

def record_audio(stream, pa, config, cobra):
    """
    Record audio from the stream until silence is detected.
    
    Args:
    stream (pyaudio.Stream): The audio stream
    pa (pyaudio.PyAudio): The PyAudio instance
    config (dict): Configuration parameters
    cobra (pvcobra.Cobra): The Cobra voice activity detection instance
    
    Returns:
    tuple: (str, float) The path to the recorded audio file and the time of the last voice detected
    """
    print("Listening...")
    audio_buffer = []
    last_voice_time = time.time()
    silent_chunks = 0
    
    while True:
        chunk = stream.read(config['CHUNK'])
        audio_buffer.append(chunk)
        
        pcm = struct.unpack_from("h" * config['CHUNK'], chunk)
        voice_probability = cobra.process(pcm)
        
        if voice_probability > config['VOICE_PROBABILITY_THRESHOLD']:
            last_voice_time = time.time()
            silent_chunks = 0
        else:
            silent_chunks += 1
        
        if silent_chunks > config['SILENT_CHUNK_THRESHOLD']:
            break
        
        if time.time() - last_voice_time > config['MAX_RECORDING_TIME']:
            break
    
    print("Finished recording")
    
    wf = wave.open("temp_audio.wav", 'wb')
    wf.setnchannels(config['CHANNELS'])
    wf.setsampwidth(pa.get_sample_size(config['FORMAT']))
    wf.setframerate(config['RATE'])
    wf.writeframes(b''.join(audio_buffer))
    wf.close()
    
    return "temp_audio.wav", last_voice_time

async def play_audio_stream(stream):
    """
    Play an audio stream using sounddevice.
    """
    # Read the entire stream into a buffer
    buffer = io.BytesIO()
    for chunk in stream:
        buffer.write(chunk)

    buffer.seek(0)
    
    # Convert the buffer to an AudioSegment
    audio = AudioSegment.from_mp3(buffer)
    playback_start_time = time.time()
    
    # Convert the AudioSegment to a numpy array
    samples = np.array(audio.get_array_of_samples())
    
    # Play the audio using sounddevice
    sd.play(samples, audio.frame_rate)
    sd.wait()  # Wait until the audio playback is finished

    return playback_start_time