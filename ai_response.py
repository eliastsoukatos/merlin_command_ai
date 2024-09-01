from openai import OpenAI

def get_ai_response(transcription, config):
    """
    Get AI response using OpenAI's GPT model.
    """
    # Initialize the OpenAI client with the API key
    client = OpenAI(api_key=config['OPENAI_API_KEY'])
    
    # Use OpenAI's chat completion API to generate a response
    response = client.chat.completions.create(
        model=config['GPT_MODEL'],  # Use the specified GPT model
        messages=[
            # Set the system message to define the AI's behavior
            {"role": "system", "content": config['SYSTEM_PROMPT']},
            # Provide the user's transcribed input
            {"role": "user", "content": transcription}
        ]
    )
    
    # Return the generated response text
    return response.choices[0].message.content