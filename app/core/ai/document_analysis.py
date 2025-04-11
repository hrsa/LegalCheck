import base64

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.analysis import AnalysisResult
from app.core.config import settings
from app.utils.formatters import format_policies_and_rules_into_text
from .ai_client import gemini_client
from .embedding_search import semantic_search


def upload_file(file_path: str):
    return gemini_client.files.upload(file=file_path)

def check_files():
    return gemini_client.files.list()

async def chat_with_document(text: str, gemini_file_name: str, db: AsyncSession):
    document = gemini_client.files.get(name=gemini_file_name)
    relevant_rules = format_policies_and_rules_into_text(await semantic_search(text=text, db=db))

    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[document, "\n\n", text],
        config={
            "system_instruction": f"Answer the user's question clearly and concisely. Don't cite the document where it's not needed. Here are some rules which may be relevant to the question:\n {relevant_rules}"
        }
    )

    return response.text

def initial_analysis(file_name, policies_and_rules):
    file = gemini_client.files.get(name=file_name)

    complete_prompt: str = base64.b64decode(settings.INITIAL_ANALYSIS_PROMPT).decode('utf-8') + policies_and_rules

    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[file, "\n\n", "Analyze the document."],
        config={
            "system_instruction": complete_prompt,
            'response_mime_type': 'application/json',
            'response_schema': AnalysisResult,
        }
    )
    return response.parsed