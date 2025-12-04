from web3 import Web3
from solcx import compile_standard, install_solc
import json
from pathlib import Path
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Install Solidity compiler
install_solc('0.8.19')

def compile_contract(contract_path: str):
    """Compile Solidity contract"""
    logger.info(f"📝 Compiling {contract_path}...")
    
    with open(contract_path, 'r') as f:
        contract_source = f.read()
    
    compiled = compile_standard({
        "language": "Solidity",
        "sources": {
            contract_path: {
                "content": contract_source
            }
        },
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                }
            }
        }
    }, solc_version="0.8.19")
    
    return compiled

def deploy_contract(w3: Web3, contract_name: str, compiled_contract, deployer_account):
    """Deploy compiled contract"""
    logger.info(f"🚀 Deploying {contract_name}...")
    
    # Get contract data
    contract_id = list(compiled_contract['contracts'].keys())[0]
    contract_data = compiled_contract['contracts'][contract_id][contract_name]
    
    bytecode = contract_data['evm']['bytecode']['object']
    abi = contract_data['abi']
    
    # Create contract instance
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Build transaction
    tx = Contract.constructor().build_transaction({
        'from': deployer_account.address,
        'nonce': w3.eth.get_transaction_count(deployer_account.address),
        'gas': 3000000,
        'gasPrice': w3.eth.gas_price
    })
    
    # Sign transaction
    signed_tx = w3.eth.account.sign_transaction(tx, deployer_account.key)
    
    # Send transaction
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    logger.info(f"⏳ Waiting for transaction receipt...")
    
    # Wait for receipt
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    contract_address = tx_receipt.contractAddress
    logger.info(f"✅ {contract_name} deployed at: {contract_address}")
    
    return contract_address, abi

def main():
    """Deploy all smart contracts"""
    logger.info("🔗 Starting smart contract deployment...")
    
    # Connect to Web3
    w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))
    
    if not w3.is_connected():
        logger.error("❌ Failed to connect to blockchain")
        return
    
    logger.info(f"✅ Connected to {settings.WEB3_PROVIDER_URL}")
    
    # Get deployer account
    deployer = w3.eth.account.from_key(settings.DEPLOYER_PRIVATE_KEY)
    logger.info(f"📝 Deploying from account: {deployer.address}")
    
    contracts_dir = Path(__file__).parent / "contracts"
    deployed_contracts = {}
    
    # Deploy AccessControl
    try:
        compiled = compile_contract(str(contracts_dir / "AccessControl.sol"))
        address, abi = deploy_contract(w3, "MedicalRecordAccessControl", compiled, deployer)
        deployed_contracts["ACCESS_CONTROL"] = {"address": address, "abi": abi}
    except Exception as e:
        logger.error(f"❌ AccessControl deployment failed: {e}")
    
    # Deploy HealthToken
    try:
        compiled = compile_contract(str(contracts_dir / "HealthToken.sol"))
        address, abi = deploy_contract(w3, "HealthToken", compiled, deployer)
        deployed_contracts["HEALTH_TOKEN"] = {"address": address, "abi": abi}
    except Exception as e:
        logger.error(f"❌ HealthToken deployment failed: {e}")
    
    # Deploy AgentCommunicationLog
    try:
        compiled = compile_contract(str(contracts_dir / "AgentCommunicationLog.sol"))
        address, abi = deploy_contract(w3, "AgentCommunicationLog", compiled, deployer)
        deployed_contracts["AGENT_LOG"] = {"address": address, "abi": abi}
    except Exception as e:
        logger.error(f"❌ AgentCommunicationLog deployment failed: {e}")
    
    # Save contract addresses and ABIs
    output_file = Path(__file__).parent / "contract_abi.json"
    with open(output_file, 'w') as f:
        json.dump(deployed_contracts, f, indent=2)
    
    logger.info(f"💾 Contract data saved to {output_file}")
    
    # Print .env update instructions
    print("\n" + "="*70)
    print("📝 UPDATE YOUR .env FILE WITH THESE VALUES:")
    print("="*70)
    for name, data in deployed_contracts.items():
        print(f"{name}_CONTRACT={data['address']}")
    print("="*70)

if __name__ == "__main__":
    main()
