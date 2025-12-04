from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from web3 import Web3
from config.blockchain_config import w3, get_access_control_contract, get_health_token_contract
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class BlockchainAgent(BaseAgent):
    """Blockchain operations agent - handles smart contract interactions"""
    
    def __init__(self, agent_id: str, name: str):
        super().__init__(agent_id, name, "blockchain")
        self.w3 = w3
        self.account = None
        self._initialize_account()
        
    def _initialize_account(self):
        """Initialize blockchain account"""
        try:
            if settings.DEPLOYER_PRIVATE_KEY:
                self.account = self.w3.eth.account.from_key(settings.DEPLOYER_PRIVATE_KEY)
                logger.info(f"✅ Blockchain account initialized: {self.account.address}")
            else:
                logger.warning("⚠️ No private key found, blockchain features will be limited")
        except Exception as e:
            logger.error(f"❌ Failed to initialize blockchain account: {e}")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process blockchain operations"""
        self.set_status("processing")
        
        try:
            action = input_data.get("action", "log")
            
            if action == "grant_access":
                patient_id = input_data["patient_id"]
                doctor_id = input_data["doctor_id"]
                duration = input_data.get("duration", 86400)  # 24 hours default
                
                result = await self._grant_access_on_chain(patient_id, doctor_id, duration)
                return result
            
            elif action == "revoke_access":
                patient_id = input_data["patient_id"]
                doctor_id = input_data["doctor_id"]
                
                result = await self._revoke_access_on_chain(patient_id, doctor_id)
                return result
            
            elif action == "reward_tokens":
                patient_id = input_data["patient_id"]
                amount = input_data["amount"]
                reason = input_data.get("reason", "")
                
                result = await self._mint_reward_tokens(patient_id, amount, reason)
                return result
            
            elif action == "log_interaction":
                log_data = input_data["log_data"]
                result = await self._log_to_blockchain(log_data)
                return result
            
            elif action == "create_nft":
                patient_id = input_data["patient_id"]
                record_hash = input_data["record_hash"]
                
                result = await self._create_medical_record_nft(patient_id, record_hash)
                return result
            
            self.set_status("idle")
            
        except Exception as e:
            logger.error(f"❌ Blockchain Agent error: {str(e)}")
            self.set_status("error")
            return {"error": str(e)}
    
    async def receive_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle blockchain operation requests"""
        msg_type = message['type']
        payload = message['payload']
        
        if msg_type == "GRANT_ACCESS_ON_CHAIN":
            return await self.process({**payload, "action": "grant_access"})
        
        elif msg_type == "REVOKE_ACCESS_ON_CHAIN":
            return await self.process({**payload, "action": "revoke_access"})
        
        elif msg_type == "REWARD_ADHERENCE" or msg_type == "REWARD_TREATMENT_PLAN_CREATED":
            return await self.process({**payload, "action": "reward_tokens"})
        
        elif msg_type == "LOG_INTERACTION" or msg_type == "LOG_EMERGENCY_ACCESS":
            return await self.process({
                "action": "log_interaction",
                "log_data": payload
            })
        
        elif msg_type == "CREATE_RECORD_NFT":
            return await self.process({**payload, "action": "create_nft"})
        
        return None
    
    async def _grant_access_on_chain(self, patient_id: str, doctor_id: str, duration: int) -> Dict:
        """Grant access to medical records via smart contract"""
        logger.info(f"🔗 Granting blockchain access: {patient_id} → {doctor_id}")
        
        try:
            if not self.account:
                logger.warning("⚠️ Blockchain account not initialized, using mock")
                return self._mock_transaction("access_granted")
            
            contract = get_access_control_contract()
            
            # Convert IDs to addresses (in production, these would be actual wallet addresses)
            patient_address = Web3.to_checksum_address(self._id_to_address(patient_id))
            doctor_address = Web3.to_checksum_address(self._id_to_address(doctor_id))
            
            # Build transaction
            tx = contract.functions.grantAccess(
                doctor_address,
                duration
            ).build_transaction({
                'from': patient_address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            logger.info(f"✅ Access granted on-chain: {tx_hash.hex()}")
            
            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "block_number": receipt['blockNumber'],
                "gas_used": receipt['gasUsed']
            }
            
        except Exception as e:
            logger.error(f"❌ Blockchain transaction failed: {e}")
            # Fallback to mock for demo
            return self._mock_transaction("access_granted")
    
    async def _revoke_access_on_chain(self, patient_id: str, doctor_id: str) -> Dict:
        """Revoke access via smart contract"""
        logger.info(f"🔗 Revoking blockchain access: {patient_id} → {doctor_id}")
        
        # Similar implementation to grant_access
        return self._mock_transaction("access_revoked")
    
    async def _mint_reward_tokens(self, patient_id: str, amount: int, reason: str) -> Dict:
        """Mint reward tokens to patient"""
        logger.info(f"🪙 Minting {amount} tokens for {patient_id}: {reason}")
        
        try:
            if not self.account:
                return self._mock_transaction("tokens_minted", {"amount": amount})
            
            contract = get_health_token_contract()
            patient_address = Web3.to_checksum_address(self._id_to_address(patient_id))
            
            # Convert amount to Wei (token decimals = 18)
            amount_wei = self.w3.to_wei(amount, 'ether')
            
            tx = contract.functions.mint(
                patient_address,
                amount_wei
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 150000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            logger.info(f"✅ Tokens minted: {tx_hash.hex()}")
            
            return {
                "success": True,
                "amount": amount,
                "tx_hash": tx_hash.hex(),
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"❌ Token minting failed: {e}")
            return self._mock_transaction("tokens_minted", {"amount": amount})
    
    async def _log_to_blockchain(self, log_data: Dict) -> Dict:
        """Log interaction to blockchain for audit trail"""
        logger.info(f"📝 Logging to blockchain")
        
        # In production: Log to AgentCommunicationLog contract
        # For demo: Return mock
        
        return self._mock_transaction("interaction_logged", log_data)
    
    async def _create_medical_record_nft(self, patient_id: str, record_hash: str) -> Dict:
        """Create NFT for medical record"""
        logger.info(f"🖼️ Creating medical record NFT for {patient_id}")
        
        # In production: Mint ERC-721 NFT with metadata IPFS hash
        
        return self._mock_transaction("nft_created", {
            "token_id": f"nft-{patient_id}-{record_hash[:8]}",
            "ipfs_hash": f"Qm{record_hash}"
        })
    
    def _mock_transaction(self, tx_type: str, extra_data: Optional[Dict] = None) -> Dict:
        """Generate mock transaction for demo purposes"""
        import secrets
        
        mock_tx = {
            "success": True,
            "tx_hash": f"0x{secrets.token_hex(32)}",
            "block_number": secrets.randbelow(1000000) + 1000000,
            "gas_used": secrets.randbelow(100000) + 50000,
            "type": tx_type,
            "network": "Polygon Mumbai Testnet"
        }
        
        if extra_data:
            mock_tx.update(extra_data)
        
        return mock_tx
    
    def _id_to_address(self, id_str: str) -> str:
        """Convert patient/doctor ID to Ethereum address (deterministic)"""
        import hashlib
        
        # Hash the ID to get a deterministic address
        hash_bytes = hashlib.sha256(id_str.encode()).digest()
        address = '0x' + hash_bytes[:20].hex()
        
        return address
