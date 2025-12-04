from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Model
    MODEL_PATH: str = "./agentfoundry-finetuned"
    BASE_MODEL: str = "BioMistral/BioMistral-7B"
    MAX_SEQ_LENGTH: int = 512
    
    # Database
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    
    # Blockchain
    WEB3_PROVIDER_URL: str
    DEPLOYER_PRIVATE_KEY: str
    ACCESS_CONTROL_CONTRACT: Optional[str] = None
    HEALTH_TOKEN_CONTRACT: Optional[str] = None
    AGENT_LOG_CONTRACT: Optional[str] = None
    
    # API Keys
    OPENAI_API_KEY: str
    ELEVENLABS_API_KEY: str
    GOOGLE_TRANSLATE_API_KEY: Optional[str] = None
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
