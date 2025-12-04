from typing import Dict, List
import asyncio
from .embeddings import embed_text
from .knowledge_bases import KnowledgeBaseManager
from .vector_store import VectorStore
from database.models import PatientHistory
from database.database import get_db
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Global knowledge base manager
_kb_manager = None

def get_kb_manager():
    """Get or create knowledge base manager"""
    global _kb_manager
    if _kb_manager is None:
        _kb_manager = KnowledgeBaseManager()
    return _kb_manager

async def retrieve_patient_context(patient_id: str, query: str, top_k: int = 5) -> str:
    """
    Retrieve relevant context for patient query using RAG
    
    Args:
        patient_id: Patient identifier
        query: Current query
        top_k: Number of relevant chunks to retrieve
        
    Returns:
        str: Formatted context string
    """
    logger.info(f"🔍 Retrieving context for patient {patient_id}")
    
    try:
        # Run retrieval tasks in parallel
        patient_history_task = asyncio.create_task(_retrieve_patient_history(patient_id, query, top_k))
        knowledge_task = asyncio.create_task(_retrieve_medical_knowledge(query, top_k))
        
        patient_history, medical_knowledge = await asyncio.gather(
            patient_history_task,
            knowledge_task
        )
        
        # Format context
        context = _format_context(patient_history, medical_knowledge)
        
        return context
        
    except Exception as e:
        logger.error(f"❌ Context retrieval error: {str(e)}")
        return "No relevant context found."

async def _retrieve_patient_history(patient_id: str, query: str, top_k: int) -> List[Dict]:
    """Retrieve relevant patient history"""
    
    try:
        # Get patient's medical history from database
        db = next(get_db())
        history_records = db.query(PatientHistory).filter(
            PatientHistory.patient_id == patient_id
        ).order_by(PatientHistory.created_at.desc()).limit(20).all()
        
        if not history_records:
            return []
        
        # Create vector store for patient history
        history_texts = []
        history_metadata = []
        
        for record in history_records:
            text = f"{record.record_type}: {record.content}"
            if record.diagnosis:
                text += f" Diagnosis: {record.diagnosis}"
            
            history_texts.append(text)
            history_metadata.append({
                'record_id': record.id,
                'date': record.created_at.isoformat() if hasattr(record, 'created_at') else None,
                'type': record.record_type
            })
        
        # Embed and search
        if history_texts:
            from .embeddings import embed_texts
            embeddings = embed_texts(history_texts)
            
            store = VectorStore(dimension=384)
            store.add_documents(history_texts, embeddings, history_metadata)
            
            query_embedding = embed_text(query)
            results = store.search(query_embedding, top_k)
            
            return [
                {
                    'text': text,
                    'score': score,
                    'metadata': metadata
                }
                for text, score, metadata in results
            ]
        
        return []
        
    except Exception as e:
        logger.error(f"❌ Patient history retrieval error: {str(e)}")
        return []

async def _retrieve_medical_knowledge(query: str, top_k: int) -> Dict[str, List]:
    """Retrieve relevant medical knowledge from knowledge bases"""
    
    try:
        kb_manager = get_kb_manager()
        query_embedding = embed_text(query)
        
        # Search across all knowledge bases
        results = kb_manager.search_all(query_embedding, top_k=top_k)
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Medical knowledge retrieval error: {str(e)}")
        return {}

def _format_context(patient_history: List[Dict], medical_knowledge: Dict[str, List]) -> str:
    """Format retrieved context into readable string"""
    
    context_parts = []
    
    # Patient History Section
    if patient_history:
        context_parts.append("PATIENT HISTORY:")
        for item in patient_history[:3]:  # Top 3
            date = item['metadata'].get('date', 'Unknown date')
            context_parts.append(f"- [{date}] {item['text']}")
    
    # Medical Knowledge Section
    if medical_knowledge:
        context_parts.append("\nRELEVANT MEDICAL KNOWLEDGE:")
        
        # Combine all knowledge base results
        all_knowledge = []
        for kb_name, results in medical_knowledge.items():
            all_knowledge.extend(results)
        
        # Sort by score (lower is better for L2 distance)
        all_knowledge.sort(key=lambda x: x[1])
        
        # Add top results
        for text, score, metadata in all_knowledge[:5]:
            context_parts.append(f"- {text}")
    
    if not context_parts:
        return "No relevant medical history or knowledge found."
    
    return "\n".join(context_parts)
