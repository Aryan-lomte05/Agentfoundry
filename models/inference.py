import torch
from typing import Optional, AsyncIterator
from transformers import TextIteratorStreamer
import threading
import asyncio
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def generate_response(
    model,
    tokenizer,
    prompt: str,
    max_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.9,
    top_k: int = 50
) -> str:
    """
    Generate response from fine-tuned model
    
    Args:
        model: Fine-tuned model
        tokenizer: Tokenizer
        prompt: Input prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        top_p: Nucleus sampling parameter
        top_k: Top-k sampling parameter
        
    Returns:
        str: Generated response
    """
    
    try:
        # Tokenize input
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(model.device)
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        # Decode
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the response (after [/INST])
        if "[/INST]" in response:
            response = response.split("[/INST]")[-1].strip()
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Generation error: {str(e)}")
        return "I apologize, but I encountered an error processing your request. Please try again."

async def generate_streaming_response(
    model,
    tokenizer,
    prompt: str,
    max_tokens: int = 256,
    temperature: float = 0.7
) -> AsyncIterator[str]:
    """
    Generate streaming response (for real-time avatar speech)
    
    Yields:
        str: Tokens as they are generated
    """
    
    try:
        # Create streamer
        streamer = TextIteratorStreamer(
            tokenizer,
            skip_special_tokens=True,
            skip_prompt=True
        )
        
        # Tokenize input
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(model.device)
        
        # Generation kwargs
        generation_kwargs = {
            **inputs,
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "do_sample": True,
            "pad_token_id": tokenizer.eos_token_id,
            "eos_token_id": tokenizer.eos_token_id,
            "streamer": streamer
        }
        
        # Start generation in separate thread
        thread = threading.Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()
        
        # Yield tokens as they come
        skip_inst = True
        for text in streamer:
            # Skip until we pass [/INST]
            if skip_inst:
                if "[/INST]" in text:
                    text = text.split("[/INST]")[-1]
                    skip_inst = False
                else:
                    continue
            
            if text:
                yield text
                await asyncio.sleep(0.01)  # Small delay for smoother streaming
        
        thread.join()
        
    except Exception as e:
        logger.error(f"❌ Streaming generation error: {str(e)}")
        yield "I apologize, but I encountered an error."
