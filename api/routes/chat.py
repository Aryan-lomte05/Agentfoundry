from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from api.schemas import ChatMessage, ChatResponse
from agents.message_bus import get_message_bus
from utils.logger import setup_logger
import json

logger = setup_logger(__name__)

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(request: Request, message: ChatMessage):
    """
    Main chat endpoint - processes patient queries
    """
    try:
        logger.info(f"💬 Chat request from patient {message.patient_id}: {message.message[:50]}...")
        
        # Get Patient Avatar Agent
        agents = request.app.state.agents
        patient_avatar = agents.get("avatar-1")
        
        if not patient_avatar:
            raise HTTPException(status_code=500, detail="Patient Avatar agent not available")
        
        # Process query
        result = await patient_avatar.process({
            "message": message.message,
            "patient_id": message.patient_id,
            "language": message.language,
            "conversation_history": message.conversation_history or []
        })
        
        # Get recent agent messages for frontend visualization
        message_bus = get_message_bus()
        agent_logs = message_bus.get_recent_messages(limit=10)
        
        return ChatResponse(
            response=result.get("response", ""),
            diagnostic_data=result.get("diagnostic_data"),
            emergency=result.get("emergency", False),
            language=message.language,
            agent_logs=agent_logs
        )
        
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def chat_stream(request: Request, message: ChatMessage):
    """
    Streaming chat endpoint for real-time avatar speech
    """
    try:
        logger.info(f"🌊 Streaming chat request from patient {message.patient_id}")
        
        async def generate():
            try:
                # Get model and tokenizer
                model = request.app.state.model
                tokenizer = request.app.state.tokenizer
                
                # Build prompt (simplified for streaming)
                from rag.retrieval import retrieve_patient_context
                context = await retrieve_patient_context(message.patient_id, message.message)
                
                prompt = f"""<s>[INST] You are a compassionate healthcare AI.

Patient History:
{context}

Question: {message.message}

Respond in {message.language}. [/INST]"""
                
                # Stream response
                from models.inference import generate_streaming_response
                async for token in generate_streaming_response(model, tokenizer, prompt):
                    yield f"data: {json.dumps({'token': token})}\n\n"
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"❌ Streaming error: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
        
    except Exception as e:
        logger.error(f"❌ Stream setup error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
