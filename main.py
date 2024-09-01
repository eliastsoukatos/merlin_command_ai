import os
import sys
import pyaudio
import wave
import struct
import time
import asyncio
import argparse
import io
from dotenv import load_dotenv
from openai import OpenAI
import pvporcupine
import pvcobra
from pathlib import Path
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import sounddevice as sd
import numpy as np
from pydub import AudioSegment

# Suppress ALSA lib warnings
stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')
import pyaudio
sys.stderr = stderr

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize Eleven Labs client
eleven_labs_client = ElevenLabs(api_key=os.getenv('ELEVEN_LABS_API_KEY'))

# Picovoice access key
PICOVOICE_ACCESS_KEY = os.getenv('PICOVOICE_ACCESS_KEY')

# Audio configuration
CHUNK = 512
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Initialize Porcupine for wake word detection
porcupine = pvporcupine.create(
    access_key=PICOVOICE_ACCESS_KEY,
    keyword_paths=[os.getenv('WAKE_WORD_PATH')]
)

# Initialize Cobra for voice activity detection
cobra = pvcobra.create(access_key=PICOVOICE_ACCESS_KEY)

# Sample questions for simulation mode
SAMPLE_QUESTIONS = [
    "What's the weather like today?",
    "Tell me a joke",
    "What's the capital of France?",
    "How do I make pasta?",
    "What's the meaning of life?"
]

def record_audio(stream, pa):
    print("Listening...")
    audio_buffer = []
    last_voice_time = time.time()
    silent_chunks = 0
    
    while True:
        chunk = stream.read(CHUNK)
        audio_buffer.append(chunk)
        
        pcm = struct.unpack_from("h" * CHUNK, chunk)
        voice_probability = cobra.process(pcm)
        
        if voice_probability > 0.5:
            last_voice_time = time.time()
            silent_chunks = 0
        else:
            silent_chunks += 1
        
        if silent_chunks > 50:  # About 1.6 seconds of silence
            break
        
        if time.time() - last_voice_time > 5:  # Max recording time of 5 seconds
            break
    
    print("Finished recording")
    
    # Save the recorded audio
    wf = wave.open("temp_audio.wav", 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(pa.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(audio_buffer))
    wf.close()
    
    return "temp_audio.wav", last_voice_time  # Return the last voice time

def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcription = openai_client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
    return transcription.text

def get_ai_response(transcription):
    response = openai_client.chat.completions.create(
        model=os.getenv('GPT_MODEL'),
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Provide concise responses."},
            {"role": "user", "content": transcription}
        ]
    )
    return response.choices[0].message.content

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

async def play_audio_stream(stream):
    buffer = io.BytesIO()
    playback_start_time = None

    for chunk in stream:
        buffer.write(chunk)

    buffer.seek(0)
    audio = AudioSegment.from_mp3(buffer)
    playback_start_time = time.time()
    
    # Convert to numpy array
    samples = np.array(audio.get_array_of_samples())
    
    # Play audio
    sd.play(samples, audio.frame_rate)
    sd.wait()

    return playback_start_time

async def process_and_play_response(transcription, speech_end_time):
    # Get AI response
    ai_response = await asyncio.to_thread(get_ai_response, transcription)
    print(f"AI Response: {ai_response}")
    
    # Convert text to speech and play audio
    audio_stream = await text_to_speech_stream(ai_response)
    playback_start_time = await play_audio_stream(audio_stream)
    
    response_time = playback_start_time - speech_end_time
    print(f"Response time (from end of speech to start of playback): {response_time:.2f} seconds")

async def simulate_interaction(question):
    print(f"Simulated question: {question}")
    speech_end_time = time.time()
    
    # Process and play response asynchronously
    await process_and_play_response(question, speech_end_time)
    
    print("Simulation complete. Press 'w' to simulate wake word, or 'q' to quit.")

async def main():
    parser = argparse.ArgumentParser(description="Voice Assistant")
    parser.add_argument("--simulate", action="store_true", help="Run in simulation mode")
    args = parser.parse_args()

    if args.simulate:
        print("Running in simulation mode. No audio input required.")
        print("Press 'w' to simulate wake word detection, or 'q' to quit.")
        
        while True:
            user_input = input().lower()
            if user_input == 'q':
                break
            elif user_input == 'w':
                print("Wake word detected!")
                for question in SAMPLE_QUESTIONS:
                    await simulate_interaction(question)
                    user_input = input().lower()
                    if user_input == 'q':
                        return
                    elif user_input != 'w':
                        print("Waiting for wake word...")
                        break
            else:
                print("Waiting for wake word...")
        return

    pa = pyaudio.PyAudio()
    audio_stream = pa.open(
        rate=RATE,
        channels=CHANNELS,
        format=FORMAT,
        input=True,
        frames_per_buffer=CHUNK
    )

    print("Waiting for wake word...")

    try:
        while True:
            pcm = audio_stream.read(CHUNK)
            pcm = struct.unpack_from("h" * CHUNK, pcm)

            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                print("Wake word detected!")
                
                # Record audio and get the end time of speech
                audio_file, speech_end_time = record_audio(audio_stream, pa)
                
                # Transcribe audio
                transcription = transcribe_audio(audio_file)
                print(f"Transcription: {transcription}")
                
                # Process and play response asynchronously
                await process_and_play_response(transcription, speech_end_time)
                
                print("Waiting for wake word...")

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        if audio_stream is not None:
            audio_stream.close()
        if pa is not None:
            pa.terminate()
        porcupine.delete()
        cobra.delete()

if __name__ == "__main__":
    asyncio.run(main())