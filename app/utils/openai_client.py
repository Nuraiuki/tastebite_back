import os
from openai import OpenAI
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

def get_openai_client():
    """Get OpenAI client with API key from environment"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        return OpenAI(api_key=api_key)
    except Exception as e:
        logger.error(f"Error creating OpenAI client: {str(e)}")
        raise 