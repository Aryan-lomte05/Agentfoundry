from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger(__name__)

class BaseAgent(ABC):
    """Base class for all healthcare AI agents"""
    
    def __init__(self, agent_id: str, name: str, specialization: str = "general"):
        self.id = agent_id
        self.name = name
        self.specialization = specialization
        self.status = "idle"  # idle, processing, error
        self.message_bus = None
        self.message_history = []
        
    def set_message_bus(self, message_bus):
        """Set the message bus for inter-agent communication"""
        self.message_bus = message_bus
        
    async def send_message(self, to_agent_id: str, message_type: str, payload: Dict[str, Any], priority: int = 3):
        """Send message to another agent"""
        if not self.message_bus:
            raise ValueError("Message bus not initialized")
            
        message = {
            "id": f"{self.id}-{datetime.now().timestamp()}",
            "from": self.id,
            "to": to_agent_id,
            "type": message_type,
            "payload": payload,
            "priority": priority,
            "timestamp": datetime.now().isoformat()
        }
        
        self.message_history.append(message)
        logger.info(f"📤 {self.name} → {message_type} → {to_agent_id}")
        
        return await self.message_bus.route_message(message)
    
    async def broadcast(self, message_type: str, payload: Dict[str, Any], priority: int = 3):
        """Broadcast message to all agents"""
        if not self.message_bus:
            raise ValueError("Message bus not initialized")
            
        return await self.message_bus.broadcast(self.id, message_type, payload, priority)
    
    @abstractmethod
    async def receive_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming message - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing logic - must be implemented by subclasses"""
        pass
    
    def set_status(self, status: str):
        """Update agent status"""
        self.status = status
        logger.info(f"🤖 {self.name} status: {status}")
