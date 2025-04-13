from datetime import datetime, timezone
from typing import Dict, Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import WebSocket, WebSocketDisconnect, HTTPException

from app.api.v1.schemas.conversation import ConversationWithMessages, MessageAuthor, MessageInDB
from app.api.v1.schemas.websocket import ChatHistoryResponse, ErrorMessage, WebSocketMessageType, NewMessageResponse
from app.api.v1.services.analysis_service import check_document_availability, upload_document_to_gemini
from app.api.v1.services.conversation_service import get_conversation, add_message, get_recent_messages
from app.api.v1.services.document_service import get_document
from app.core.ai.document_analysis import chat_with_document
from app.core.websocket_manager import ConnectionManager
from app.db.models import Document
from app.utils.formatters import format_messages_history

manager = ConnectionManager()


async def handle_websocket_connection(
        websocket: WebSocket,
        conversation_id: int,
        user_id: int,
        db: AsyncSession
):
    try:
        conversation = await get_conversation(db, conversation_id=conversation_id)
        document = await get_document(db, document_id=conversation.document_id)
        if not conversation or conversation.user_id != user_id:
            await websocket.close(code=4003, reason="Access denied to conversation")
            return

        if not document:
            await websocket.close(code=4004, reason="Document not found")
        if not document.is_processed or document.gemini_name is None:
            await websocket.close(code=4005, reason="Document is not processed yet")
        if not check_document_availability(document):
            document = await upload_document_to_gemini(db, document.id)

        await manager.connect(websocket, user_id, conversation_id)

        history_message = ChatHistoryResponse(
            conversation_id=conversation_id,
            payload=ConversationWithMessages.model_validate(conversation, from_attributes=True)
        )
        await websocket.send_json(history_message.model_dump(mode="json"))

        while True:
            data = await websocket.receive_json()
            await process_client_message(websocket, data, db, conversation_id, document, user_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, conversation_id)
    except HTTPException as e:
        error_message = ErrorMessage(
            conversation_id=conversation_id,
            payload={"message": e.detail, "status_code": e.status_code}
        )
        await websocket.send_json(error_message.model_dump(mode="json"))
        await websocket.close(code=4000 + e.status_code, reason=e.detail)
    except Exception as e:
        logger.error(f"Error processing websocket connection: {str(e)}")
        error_message = ErrorMessage(
            conversation_id=conversation_id,
            payload={"message": f"An error occurred: {str(e)}"}
        )
        try:
            await websocket.send_json(error_message.model_dump(mode="json"))
            await websocket.close(code=1011)
        except Exception as e:
            logger.error(f"Error sending error message: {str(e)}")
            pass
        manager.disconnect(websocket, user_id, conversation_id)


async def process_client_message(
        websocket: WebSocket,
        data: Dict[str, Any],
        db: AsyncSession,
        conversation_id: int,
        document: Document,
        user_id: int
):
    message_type = data.get("type")

    if message_type == WebSocketMessageType.NEW_MESSAGE:
        content = data.get("content")
        if not content:
            error = ErrorMessage(
                conversation_id=conversation_id,
                payload={"message": "Message content is required"}
            )
            await websocket.send_json(error.model_dump(mode="json"))
            return

        user_message = await add_message(
            db,
            conversation_id,
            content,
            MessageAuthor.user
        )

        message_response = NewMessageResponse(
            conversation_id=conversation_id,
            payload=MessageInDB.model_validate(user_message, from_attributes=True)
        )
        await websocket.send_json(message_response.model_dump(mode="json"))

        recent_messages = await get_recent_messages(db, conversation_id, 10)
        if recent_messages:
            history = format_messages_history(recent_messages)
        else:
            history = None

        ai_response = await chat_with_document(text=content, gemini_file_name=document.gemini_name, db=db, history=history)

        ai_message = await add_message(
            db,
            conversation_id,
            ai_response,
            MessageAuthor.legalcheck
        )

        ai_message_response = NewMessageResponse(
            conversation_id=conversation_id,
            payload=MessageInDB.model_validate(ai_message, from_attributes=True)
        )
        await websocket.send_json(ai_message_response.model_dump(mode="json"))

    elif message_type == WebSocketMessageType.PING:
        await websocket.send_json({
            "type": WebSocketMessageType.PONG,
            "conversation_id": conversation_id,
            "timestamp": str(datetime.now(timezone.utc))
        })
