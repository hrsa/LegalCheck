import sentry_sdk
from fastapi import FastAPI, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.v1.routers.analysis import router as analysis_router
from app.api.v1.routers.document import router as document_router
from app.api.v1.routers.policy import router as policy_router
from app.api.v1.routers.rule import router as rule_router
from app.core.config import settings
from app.db.models import Document
from app.db.session import get_async_session

sentry_sdk.init(
    dsn=settings.SENTRY_DSN_URL,
    send_default_pii=True,
    traces_sample_rate=1.0,
    _experiments={
        "continuous_profiling_auto_start": True,
    },
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(policy_router, prefix="/api/v1/policies", tags=["policies"])
app.include_router(document_router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(analysis_router, prefix="/api/v1/documents", tags=["analysis"])
app.include_router(rule_router, prefix="/api/v1/rules", tags=["rules"])

analysis_results = {}


@app.get("/")
def read_root():
    return {"message": "Welcome to LegalCheck API"}

@app.post("/")
async def reply(doc: int = Form(...), message: str = Form(...), db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(Document).filter(Document.id == doc))
    document = result.scalar_one_or_none()
    # print(document.file_path)
    # dp = DocumentProcessor()
    # text = dp.process_document(file_path=document.file_path)
    # answer = semantic_search(db, text)
    # answer = upload_file(document.file_path, message)
    return {"answer": answer}
