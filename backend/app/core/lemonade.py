"""
Module for generating embeddings using an asynchronous OpenAI-compatible client.

This module initializes an async client for local or remote LLM inference
(e.g., LLMade, Ollama) and provides a high-level function to generate
vector embeddings for text inputs.
"""
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
load_dotenv()

# Default to standard local ports, but allow overrides via .env
LEMONADE_URL = os.getenv("LEMONADE_AI_URL", "http://localhost:13305/v1")
LEMONADE_API_KEY = os.getenv("LEMONADE_API_KEY", "sk-local-dummy-key")

# We pass a dummy API key because local instances still expect the header,
# even if they don't validate it.
# Async used because we have many embeddings to calculate that don't rely on
# each other to finish before the next can be calculated.
ai_client = AsyncOpenAI(
    base_url=LEMONADE_URL,
    api_key=LEMONADE_API_KEY
)

async def generate_embedding(text: str, model_name: str = "nomic-embed-text-v1.5-GGUF-Q4_K_M") -> list[float]:
    """
    Generates a vector embedding for a given string of text.

    Uses an asynchronous OpenAI-compatible client to request embeddings
    from the configured LLM endpoint (e.g., Nomic Text-Embedding).

    Args:
        text: The input string to embed.
        model_name: The name of the embedding model to use. Defaults to
            "nomic-embed-text-v1.5-GGUF-Q4_K_M".

    Returns:
        A list of floats representing the vector embedding of the input text.

    Raises:
        Exception: If the API call fails or returns an unexpected response.
    """
    response = await ai_client.embeddings.create(
        input=text,
        model=model_name
    )
    return response.data[0].embedding