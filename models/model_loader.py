import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
from config.settings import settings
from utils.logger import setup_logger
import asyncio

logger = setup_logger(__name__)

async def load_model():
    """
    Load fine-tuned BioMistral model with LoRA adapters
    
    Returns:
        tuple: (model, tokenizer)
    """
    logger.info("🧠 Loading BioMistral-7B with fine-tuned LoRA adapters...")
    
    try:
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        model, tokenizer = await loop.run_in_executor(None, _load_model_sync)
        
        logger.info("✅ Model loaded successfully!")
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"❌ Failed to load model: {str(e)}")
        raise

def _load_model_sync():
    """Synchronous model loading (runs in thread pool)"""
    
    # 4-bit quantization config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True
    )
    
    # Load base model
    logger.info(f"📦 Loading base model: {settings.BASE_MODEL}")
    base_model = AutoModelForCausalLM.from_pretrained(
        settings.BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16
    )
    
    # Load LoRA adapters
    logger.info(f"🔧 Loading LoRA adapters from: {settings.MODEL_PATH}")
    model = PeftModel.from_pretrained(base_model, settings.MODEL_PATH)
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(settings.BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    # Set to evaluation mode
    model.eval()
    
    logger.info(f"📊 Model ready - Max sequence length: {settings.MAX_SEQ_LENGTH}")
    
    return model, tokenizer
