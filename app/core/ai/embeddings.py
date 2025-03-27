from google.genai import types
from google.genai.types import ContentEmbedding

from .ai_client import openai_client
from .ai_client import gemini_client


def get_embedding_openai(text):
    response = openai_client.embeddings.create(input=text, model="text-embedding-ada-002")
    print(response.usage)
    return response.data[0].embedding


def get_embedding_gemini(text) -> ContentEmbedding:
    response = gemini_client.models.embed_content(
        model="gemini-embedding-exp-03-07",
        contents=text,
        config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")
    )
    vector = response.embeddings[0].values

    return vector
