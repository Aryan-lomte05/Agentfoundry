import asyncio
from typing import Dict, List, Any
from collections import defaultdict
import heapq
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger(__name__)

class MessageBus:
    """Central message bus for agent-to-agent communication"""
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.message_queue = []  # Priority queue
        self.message_log: List[Dict] = []
        self.recent_messages: List[Dict] = []  # Last 100 messages for WebSocket
        self.subscriptions = defaultdict(list)  # event_type -> [agent_ids]
        
    def register_agent(self, agent):
        """Register an agent with the message bus"""
        self.agents[agent.id] = agent
        agent.set_message_bus(self)
        logger.info(f"✅ Registered agent: {agent.name} ({agent.id})")
        
    async def route_message(self, message: Dict[str, Any]) -> Any:
        """Route message to recipient agent"""
        recipient_id = message['to']
        
        if recipient_id not in self.agents:
            logger.error(f"❌ Recipient not found: {recipient_id}")
            return None
        
        # Log message
        self.message_log.append(message)
        self.recent_messages.append(message)
        if len(self.recent_messages) > 100:
            self.recent_messages.pop(0)
        
        # Priority routing
        priority = message.get('priority', 3)
        if priority == 1:  # CRITICAL - immediate processing
            return await self._process_immediate(message)
        else:
            # Add to queue
            heapq.heappush(self.message_queue, (priority, message))
            return await self._process_queue()
    
    async def _process_immediate(self, message: Dict[str, Any]) -> Any:
        """Process critical message immediately"""
        recipient = self.agents[message['to']]
        logger.warning(f"🚨 CRITICAL MESSAGE: {message['type']} → {recipient.name}")
        return await recipient.receive_message(message)
    
    async def _process_queue(self):
        """Process messages from priority queue"""
        if not self.message_queue:
            return None
            
        priority, message = heapq.heappop(self.message_queue)
        recipient = self.agents[message['to']]
        return await recipient.receive_message(message)
    
    async def broadcast(self, from_agent_id: str, event_type: str, payload: Dict[str, Any], priority: int = 3):
        """Broadcast message to all subscribed agents"""
        subscribers = self.subscriptions.get(event_type, [])
        
        logger.info(f"📡 Broadcasting {event_type} to {len(subscribers)} agents")
        
        results = []
        for agent_id in subscribers:
            if agent_id != from_agent_id:  # Don't send to self
                message = {
                    "id": f"broadcast-{datetime.now().timestamp()}",
                    "from": from_agent_id,
                    "to": agent_id,
                    "type": event_type,
                    "payload": payload,
                    "priority": priority,
                    "timestamp": datetime.now().isoformat()
                }
                result = await self.route_message(message)
                results.append(result)
        
        return results
    
    def subscribe(self, agent_id: str, event_type: str):
        """Subscribe agent to event type"""
        self.subscriptions[event_type].append(agent_id)
        logger.info(f"📮 {agent_id} subscribed to {event_type}")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            agent_id: {
                "name": agent.name,
                "status": agent.status,
                "specialization": agent.specialization,
                "message_count": len(agent.message_history)
            }
            for agent_id, agent in self.agents.items()
        }
    
    def get_recent_messages(self, limit: int = 50) -> List[Dict]:
        """Get recent messages for frontend visualization"""
        return self.recent_messages[-limit:]

# Global message bus instance
_message_bus = None

def get_message_bus() -> MessageBus:
    global _message_bus
    if _message_bus is None:
        _message_bus = MessageBus()
    return _message_bus
