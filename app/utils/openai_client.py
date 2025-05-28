import os
from openai import OpenAI

def get_openai_client():
    """
    Creates and returns an OpenAI client instance.
    The client is initialized with the API key from environment variables.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key, base_url="https://api.openai.com/v1") 