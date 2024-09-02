import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_ai_response(transcription):

    response = openai_client.chat.completions.create(
        model=os.getenv('GPT_MODEL'),
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Provide concise responses."},
            {"role": "user", "content": transcription}
        ]
    )
    return response.choices[0].message.content