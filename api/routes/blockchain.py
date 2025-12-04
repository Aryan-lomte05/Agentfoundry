from fastapi import APIRouter, HTTPException, Request
from api.schemas import AccessGrantRequest, TokenRewardRequest
from utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

@router.post("/grant-access")
async def grant_access(request: Request, access_request: AccessGrantRequest):
    """Grant doctor access to patient records"""
    try:
        logger.info(f"🔓 Access grant request: {access_request.patient_id} → {access_request.doctor_id}")
        
        # Get blockchain agent
        agents = request.app.state.agents
        blockchain_agent = agents.get("chain-1")
        
        if not blockchain_agent:
            raise HTTPException(status_code=500, detail="Blockchain agent not available")
        
        # Process access grant
        result = await blockchain_agent.process({
            "action": "grant_access",
            "patient_id": access_request.patient_id,
            "doctor_id": access_request.doctor_id,
            "duration": access_request.duration_hours * 3600
        })
        
        return {
            "success": True,
            "message": f"Access granted for {access_request.duration_hours} hours",
            "transaction": result
        }
        
    except Exception as e:
        logger.error(f"❌ Access grant error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/revoke-access")
async def revoke_access(request: Request, patient_id: str, doctor_id: str):
    """Revoke doctor access"""
    try:
        logger.info(f"🔒 Access revoke request: {patient_id} → {doctor_id}")
        
        agents = request.app.state.agents
        blockchain_agent = agents.get("chain-1")
        
        if not blockchain_agent:
            raise HTTPException(status_code=500, detail="Blockchain agent not available")
        
        result = await blockchain_agent.process({
            "action": "revoke_access",
            "patient_id": patient_id,
            "doctor_id": doctor_id
        })
        
        return {
            "success": True,
            "message": "Access revoked successfully",
            "transaction": result
        }
        
    except Exception as e:
        logger.error(f"❌ Access revoke error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reward-tokens")
async def reward_tokens(request: Request, reward: TokenRewardRequest):
    """Reward patient with health tokens"""
    try:
        logger.info(f"🪙 Token reward request: {reward.patient_id} - {reward.amount} tokens")
        
        agents = request.app.state.agents
        blockchain_agent = agents.get("chain-1")
        
        if not blockchain_agent:
            raise HTTPException(status_code=500, detail="Blockchain agent not available")
        
        result = await blockchain_agent.process({
            "action": "reward_tokens",
            "patient_id": reward.patient_id,
            "amount": reward.amount,
            "reason": reward.reason
        })
        
        return {
            "success": True,
            "message": f"Rewarded {reward.amount} tokens",
            "transaction": result
        }
        
    except Exception as e:
        logger.error(f"❌ Token reward error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/balance/{patient_id}")
async def get_token_balance(patient_id: str):
    """Get patient's token balance"""
    try:
        # In production: Query blockchain smart contract
        # For demo: Return mock balance
        
        return {
            "patient_id": patient_id,
            "balance": 150,  # Mock balance
            "currency": "HLTH",
            "last_updated": "2024-11-30T12:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"❌ Balance query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions/{patient_id}")
async def get_transactions(patient_id: str, limit: int = 10):
    """Get patient's blockchain transaction history"""
    try:
        # Mock transaction history
        transactions = [
            {
                "tx_hash": "0xabc123...",
                "type": "reward",
                "amount": 10,
                "reason": "7-day medication adherence",
                "timestamp": "2024-11-29T10:00:00Z"
            },
            {
                "tx_hash": "0xdef456...",
                "type": "reward",
                "amount": 20,
                "reason": "Treatment plan completion",
                "timestamp": "2024-11-28T15:30:00Z"
            }
        ]
        
        return {
            "patient_id": patient_id,
            "count": len(transactions),
            "transactions": transactions
        }
        
    except Exception as e:
        logger.error(f"❌ Transactions query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
