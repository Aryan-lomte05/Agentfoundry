import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:", response.json())

def test_chat():
    """Test chat endpoint"""
    data = {
        "message": "I have fever and headache for 3 days",
        "patient_id": "PAT-TEST-001",
        "language": "en"
    }
    
    response = requests.post(f"{BASE_URL}/api/chat/", json=data)
    print("Chat Response:", json.dumps(response.json(), indent=2))

def test_agents():
    """Test agent status"""
    response = requests.get(f"{BASE_URL}/api/agents/status")
    print("Agent Status:", json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    print("🧪 Testing HealthFourUs API...\n")
    
    test_health()
    print("\n" + "="*70 + "\n")
    
    test_agents()
    print("\n" + "="*70 + "\n")
    
    test_chat()
