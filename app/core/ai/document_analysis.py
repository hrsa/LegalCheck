import base64
from typing import Optional

from google.genai.types import Tool, GoogleSearch, GenerateContentConfig
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.analysis import AnalysisResult
from app.core.config import settings
from app.utils.formatters import format_policies_and_rules_into_text, print_model
from .ai_client import gemini_client
from .embedding_search import semantic_search


def upload_file(file_path: str):
    return gemini_client.files.upload(file=file_path)


def check_files():
    return gemini_client.files.list()


async def chat_with_document(text: str, gemini_file_name: str, db: AsyncSession, history: Optional[str] = None):
    google_search_tool = Tool(
        google_search=GoogleSearch()
    )
    document = gemini_client.files.get(name=gemini_file_name)
    relevant_rules = format_policies_and_rules_into_text(await semantic_search(text=text, db=db))
    system_instruction = f"You are LegalCheck - an expert AI for legal teams. Answer the user's question clearly and concisely. Don't cite the document where it's not needed. Here are some rules which may be relevant to the question:\n {relevant_rules}"
    if history:
        system_instruction += f"\n\nPrevious conversation:\n{history}"

    response = gemini_client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=[document, "\n\n", text],
        config=GenerateContentConfig(
            tools=[google_search_tool],
            response_modalities=["TEXT"],
            system_instruction=[system_instruction]
        )
    )

    return response.text


def initial_analysis(file_name, policies_and_rules):
    file = gemini_client.files.get(name=file_name)

    complete_prompt: str = base64.b64decode(settings.INITIAL_ANALYSIS_PROMPT).decode('utf-8') + policies_and_rules

    response = gemini_client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=[file, "\n\n", "Analyze the document."],
        config={
            "system_instruction": complete_prompt,
            'response_mime_type': 'application/json',
            'response_schema': AnalysisResult,
        }
    )
    return response.parsed
