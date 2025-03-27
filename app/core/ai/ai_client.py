from openai import OpenAI
from google import genai
from app.core.config import settings

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
