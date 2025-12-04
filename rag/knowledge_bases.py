from typing import Dict, List
import json
from pathlib import Path
from .embeddings import embed_texts
from .vector_store import VectorStore
from utils.logger import setup_logger

logger = setup_logger(__name__)

class KnowledgeBaseManager:
    """Manage multiple medical knowledge bases"""
    
    def __init__(self, base_dir: str = "./knowledge_bases"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.stores: Dict[str, VectorStore] = {}
        
        # Initialize knowledge bases
        self._initialize_knowledge_bases()
    
    def _initialize_knowledge_bases(self):
        """Initialize all knowledge base vector stores"""
        kb_configs = {
            'medical_knowledge': {
                'description': 'General medical knowledge',
                'sample_data': [
                    "Fever is a common symptom of many infections including malaria, dengue, and COVID-19.",
                    "Diabetes mellitus is characterized by high blood sugar levels. Type 2 diabetes is managed with metformin.",
                    "Hypertension (high blood pressure) can be controlled with lifestyle changes and medications like amlodipine.",
                    "Tuberculosis is a bacterial infection that primarily affects the lungs. Treatment involves AKT-4 regimen.",
                    "Dengue fever is transmitted by Aedes mosquitoes. Symptoms include high fever, body pain, and rash.",
                    "Malaria is caused by Plasmodium parasites. Treatment includes artemisinin-based combinations.",
                    "COVID-19 can cause respiratory symptoms. Vaccination is important for prevention.",
                    "Paracetamol is a common pain reliever and fever reducer. Safe dose is 500-1000mg every 6 hours.",
                ]
            },
            'indian_diseases': {
                'description': 'India-specific disease information',
                'sample_data': [
                    "Malaria is endemic in many parts of India, especially during monsoon season.",
                    "Dengue outbreaks are common in urban areas of India during post-monsoon period.",
                    "Tuberculosis remains a major health challenge in India. Free treatment available under DOTS program.",
                    "Typhoid fever is common in areas with poor sanitation. Vaccination available.",
                    "Japanese Encephalitis is prevalent in rural areas. Vaccination recommended.",
                    "Chikungunya is transmitted by mosquitoes, causes joint pain and fever.",
                    "Leptospirosis can occur after floods. Symptoms include fever and muscle pain.",
                ]
            },
            'medications': {
                'description': 'Medication information',
                'sample_data': [
                    "Paracetamol (acetaminophen): 500mg every 6 hours. Safe for fever and pain.",
                    "Amoxicillin: 500mg three times daily. Common antibiotic for bacterial infections.",
                    "Metformin: 500mg with meals. First-line treatment for type 2 diabetes.",
                    "Amlodipine: 5mg once daily. Used for hypertension and angina.",
                    "Azithromycin: 500mg once daily for 3 days. Broad-spectrum antibiotic.",
                    "Ibuprofen: 400mg every 8 hours. Anti-inflammatory and pain reliever.",
                    "Artemether-Lumefantrine: Anti-malarial combination therapy.",
                    "AKT-4 contains Rifampicin, Isoniazid, Pyrazinamide, Ethambutol for tuberculosis.",
                ]
            },
            'government_programs': {
                'description': 'Indian government healthcare programs',
                'sample_data': [
                    "Ayushman Bharat provides health insurance coverage up to ₹5 lakh for poor families.",
                    "RSBY (Rashtriya Swasthya Bima Yojana) offers cashless health insurance.",
                    "Janani Suraksha Yojana promotes institutional delivery and provides cash assistance.",
                    "National Tuberculosis Elimination Program provides free TB diagnosis and treatment.",
                    "Mission Indradhanush aims to achieve full immunization coverage.",
                    "Pradhan Mantri Jan Arogya Yojana covers secondary and tertiary care hospitalization.",
                    "108 Ambulance Service provides free emergency medical transport.",
                    "102 is the medical helpline number for non-emergency medical advice.",
                ]
            }
        }
        
        for kb_name, config in kb_configs.items():
            kb_path = self.base_dir / kb_name
            
            # Try to load existing
            if kb_path.with_suffix('.index').exists():
                logger.info(f"📂 Loading existing knowledge base: {kb_name}")
                self.stores[kb_name] = VectorStore.load(str(kb_path))
            else:
                # Create new
                logger.info(f"🔧 Creating new knowledge base: {kb_name}")
                store = VectorStore(dimension=384)
                
                # Add sample data
                embeddings = embed_texts(config['sample_data'])
                metadata = [{'source': kb_name, 'type': 'sample'} for _ in config['sample_data']]
                store.add_documents(config['sample_data'], embeddings, metadata)
                
                # Save
                store.save(str(kb_path))
                self.stores[kb_name] = store
        
        logger.info(f"✅ Initialized {len(self.stores)} knowledge bases")
    
    def search_all(self, query_embedding, top_k: int = 3) -> Dict[str, List]:
        """Search across all knowledge bases"""
        results = {}
        
        for kb_name, store in self.stores.items():
            results[kb_name] = store.search(query_embedding, top_k)
        
        return results
    
    def add_to_knowledge_base(self, kb_name: str, texts: List[str], metadata: List[Dict] = None):
        """Add documents to specific knowledge base"""
        if kb_name not in self.stores:
            logger.warning(f"Knowledge base {kb_name} not found")
            return
        
        embeddings = embed_texts(texts)
        self.stores[kb_name].add_documents(texts, embeddings, metadata)
        
        # Save updated store
        kb_path = self.base_dir / kb_name
        self.stores[kb_name].save(str(kb_path))
