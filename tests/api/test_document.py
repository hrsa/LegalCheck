import os
import tempfile

import pytest
import requests

from app.api.v1.services.document_service import get_document, ocr_document
from app.core.config import settings
from tests.conftest import new_user, login, logout

email = "doc_test@test.com"
password = "securepassword123"

@pytest.mark.asyncio(loop_scope="package")
async def test_ensures_fresh_db(fresh_db_session):
    pass

@pytest.mark.asyncio(loop_scope="package")
async def test_upload_document(async_client, document_type: str = "text"):

    if document_type == "text":
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(b"This is a test document content.")
            temp_file_path = temp_file.name
            file_type = "text/plain"
    elif document_type == "image" :
        image_url = "https://placehold.co/600x400/orange/blue/png?text=This+is+a+test+for+LegalCheck+to+recognize+images"
        img_response = requests.get(image_url)
        assert img_response.status_code == 200, f"Failed to download test image, status code {img_response.status_code}"
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file.write(img_response.content)
            temp_file_path = temp_file.name
            file_type = "image/png"

    await new_user(async_client,email, password)
    await login(async_client, email, password)

    try:
        with open(temp_file_path, "rb") as file:
            files = {"file": (os.path.basename(temp_file_path), file, file_type)}
            data = {"company_id": 1}
            response = await async_client.post(
                f"{settings.API_V1_STR}/documents/", 
                files=files,
                data=data
            )

        assert response.status_code == 200, f"Unexpected status code: {response.status_code}"

        response_json = response.json()
        assert "id" in response_json, "Response missing document id"
        if document_type == "text":
            assert response_json["filename"].endswith(".txt"), "Filename should end with .txt"
            assert response_json["content_type"] == "text/plain"
        elif document_type == "image":
            assert response_json["filename"].endswith(".png"), "Filename should end with .png"
            assert response_json["content_type"] == "image/png"
        assert response_json["company_id"] == 1
        assert response_json["is_processed"] is False

        # Store document_id for later tests
        document_id = response_json["id"]

        return document_id

    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@pytest.mark.asyncio(loop_scope="package")
async def test_get_all_documents(async_client):
    await login(async_client, email, password)

    # Get all documents
    response = await async_client.get(f"{settings.API_V1_STR}/documents/")

    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"

    documents = response.json()
    assert isinstance(documents, list), "Response should be a list"

    # If we have documents, check the structure of the first one
    if documents:
        document = documents[0]
        assert "id" in document, "Document missing id"
        assert "filename" in document, "Document missing filename"
        assert "content_type" in document, "Document missing content_type"
        assert "company_id" in document, "Document missing company_id"
        assert "is_processed" in document, "Document missing is_processed"
        assert "created_at" in document, "Document missing created_at"


@pytest.mark.asyncio(loop_scope="package")
async def test_get_document_by_id(async_client):

    document_id = await test_upload_document(async_client)

    response = await async_client.get(f"{settings.API_V1_STR}/documents/{document_id}")

    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"

    document = response.json()
    assert document["id"] == document_id, "Document ID doesn't match"
    assert "filename" in document, "Document missing filename"
    assert "content_type" in document, "Document missing content_type"
    assert "company_id" in document, "Document missing company_id"
    assert "is_processed" in document, "Document missing is_processed"
    assert "created_at" in document, "Document missing created_at"

    return document


@pytest.mark.asyncio(loop_scope="package")
async def test_get_nonexistent_document(async_client):
    await login(async_client, email, password)

    # Try to get a document with a non-existent ID
    response = await async_client.get(f"{settings.API_V1_STR}/documents/99999")

    assert response.status_code == 404, f"Expected 404, got: {response.status_code}"
    assert "detail" in response.json(), "Response missing error message"
    assert response.json()["detail"] == "Document not found"


@pytest.mark.asyncio(loop_scope="package")
async def test_delete_document(async_client):

    document_id = await test_upload_document(async_client)


    response = await async_client.delete(f"{settings.API_V1_STR}/documents/{document_id}")

    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    assert "detail" in response.json(), "Response missing success message"
    assert f"Document {document_id} deleted successfully" in response.json()["detail"]

    get_response = await async_client.get(f"{settings.API_V1_STR}/documents/{document_id}")
    assert get_response.status_code == 404, f"Expected 404, got: {get_response.status_code}"


@pytest.mark.asyncio(loop_scope="package")
async def test_delete_nonexistent_document(async_client):
    await login(async_client, email, password)

    # Try to delete a document with a non-existent ID
    response = await async_client.delete(f"{settings.API_V1_STR}/documents/99999")

    assert response.status_code == 404, f"Expected 404, got: {response.status_code}"
    assert "detail" in response.json(), "Response missing error message"
    assert response.json()["detail"] == "Document not found"


@pytest.mark.asyncio(loop_scope="package")
async def test_unauthorized_access(async_client):
    await logout(async_client)

    response = await async_client.get(f"{settings.API_V1_STR}/documents/")

    assert response.status_code == 401, f"Expected 401, got: {response.status_code}"
    assert "detail" in response.json(), "Response missing error message"
    assert response.json()["detail"] == "Unauthorized"


@pytest.mark.asyncio(loop_scope="package")
async def test_ocr_document(async_client, db_session):
        text_document_id = await test_upload_document(async_client, "text")
        image_document_id = await test_upload_document(async_client, "image")

        await ocr_document(db=db_session, document_id=text_document_id)
        await ocr_document(db=db_session, document_id=image_document_id)

        text_document = await get_document(db=db_session, document_id=text_document_id)
        assert text_document.text_content == "This is a test document content.", f"Document content is different from expected: {text_document.text_content}"

        image_document = await get_document(db=db_session, document_id=image_document_id)
        assert image_document.text_content == "This is a test for LegalCheck to recognize images", f"Document content is different from expected: {image_document.text_content}"





