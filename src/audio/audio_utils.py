import time
import wave
import struct
import numpy as np
from pydub import AudioSegment
import io
import pyaudio
import asyncio
from pydub.playback import play
from io import BytesIO
import os
import sys
import subprocess

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
    Play audio from a stream using mpg123, avoiding ALSA errors.
    """
    # Create a temporary file to store the audio
    temp_file = "temp_response.mp3"
    
    try:
        # Write the stream to a temporary file
        with open(temp_file, 'wb') as f:
            if hasattr(stream, '__aiter__'):  # Check if it's an async iterator
                async for chunk in stream:
                    f.write(chunk)
            else:  # It's a regular generator
                for chunk in stream:
                    f.write(chunk)
        
        # Start time for performance measurement
        playback_start_time = time.time()
        
        # Use mpg123 player which is more reliable than sounddevice
        # Redirect all output to /dev/null to suppress any errors
        with open(os.devnull, 'w') as DEVNULL:
            process = await asyncio.create_subprocess_exec(
                'mpg123', '-q', temp_file,
                stdout=DEVNULL,
                stderr=DEVNULL
            )
            
            # Wait for playback to complete
            await process.wait()
        
    except Exception as e:
        # Fall back to silent non-playing if mpg123 fails
        # This is better than failing completely
        print(f"Audio playback error (silent fail): {str(e)[:100]}")
        playback_start_time = time.time()
        # Simulate a delay to mimic audio playing
        await asyncio.sleep(1)
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
    
    return playback_start_time