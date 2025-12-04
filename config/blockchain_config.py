from web3 import Web3
from config.settings import settings

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))

# Contract ABIs (will be populated after deployment)
ACCESS_CONTROL_ABI = []  # Load from contract_abi.json
HEALTH_TOKEN_ABI = []
AGENT_LOG_ABI = []

def get_access_control_contract():
    if not settings.ACCESS_CONTROL_CONTRACT:
        raise ValueError("ACCESS_CONTROL_CONTRACT not set in .env")
    return w3.eth.contract(
        address=Web3.to_checksum_address(settings.ACCESS_CONTROL_CONTRACT),
        abi=ACCESS_CONTROL_ABI
    )

def get_health_token_contract():
    if not settings.HEALTH_TOKEN_CONTRACT:
        raise ValueError("HEALTH_TOKEN_CONTRACT not set in .env")
    return w3.eth.contract(
        address=Web3.to_checksum_address(settings.HEALTH_TOKEN_CONTRACT),
        abi=HEALTH_TOKEN_ABI
    )

def get_agent_log_contract():
    if not settings.AGENT_LOG_CONTRACT:
        raise ValueError("AGENT_LOG_CONTRACT not set in .env")
    return w3.eth.contract(
        address=Web3.to_checksum_address(settings.AGENT_LOG_CONTRACT),
        abi=AGENT_LOG_ABI
    )
