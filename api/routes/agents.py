from fastapi import APIRouter, HTTPException, Request
from api.schemas import AgentStatus, AgentMessage
from agents.message_bus import get_message_bus
from typing import List
from utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

@router.get("/status", response_model=List[AgentStatus])
async def get_agents_status(request: Request):
    """Get status of all agents"""
    try:
        message_bus = get_message_bus()
        status_data = message_bus.get_agent_status()
        
        agents = []
        for agent_id, data in status_data.items():
            agents.append(AgentStatus(
                agent_id=agent_id,
                name=data['name'],
                status=data['status'],
                specialization=data['specialization'],
                message_count=data['message_count']
            ))
        
        return agents
        
    except Exception as e:
        logger.error(f"❌ Agent status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages", response_model=List[AgentMessage])
async def get_agent_messages(limit: int = 50):
    """Get recent agent-to-agent messages"""
    try:
        message_bus = get_message_bus()
        messages = message_bus.get_recent_messages(limit)
        
        return [
            AgentMessage(
                id=msg['id'],
                from_agent=msg['from'],
                to_agent=msg['to'],
                type=msg['type'],
                timestamp=msg['timestamp'],
                priority=msg['priority']
            )
            for msg in messages
        ]
        
    except Exception as e:
        logger.error(f"❌ Messages retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_id}")
async def get_agent_details(agent_id: str, request: Request):
    """Get detailed information about specific agent"""
    try:
        agents = request.app.state.agents
        
        if agent_id not in agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = agents[agent_id]
        
        return {
            "agent_id": agent.id,
            "name": agent.name,
            "specialization": agent.specialization,
            "status": agent.status,
            "message_history_count": len(agent.message_history),
            "recent_messages": agent.message_history[-10:] if agent.message_history else []
        }
        
    except Exception as e:
        logger.error(f"❌ Agent details error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-communication")
async def test_agent_communication(request: Request):
    """Test agent-to-agent communication"""
    try:
        logger.info("🧪 Testing agent communication")
        
        agents = request.app.state.agents
        patient_avatar = agents.get("avatar-1")
        diagnostic_agent = agents.get("diag-1")
        
        if not patient_avatar or not diagnostic_agent:
            raise HTTPException(status_code=500, detail="Agents not available")
        
        # Send test message
        result = await patient_avatar.send_message(
            "diag-1",
            "TEST_MESSAGE",
            {"test": "data", "timestamp": "now"},
            priority=3
        )
        
        return {
            "success": True,
            "message": "Test message sent successfully",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"❌ Communication test error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
