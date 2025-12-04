from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Patient(Base):
    """Patient model"""
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    age = Column(Integer)
    gender = Column(String(20))
    phone = Column(String(20))
    location = Column(JSON)  # Store as JSON: {"lat": ..., "lng": ..., "address": ...}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    history = relationship("PatientHistory", back_populates="patient")
    medical_records = relationship("MedicalRecord", back_populates="patient")
    
    def __repr__(self):
        return f"<Patient(patient_id={self.patient_id}, name={self.name})>"

class PatientHistory(Base):
    """Patient medical history"""
    __tablename__ = "patient_history"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(100), ForeignKey("patients.patient_id"), nullable=False, index=True)
    record_type = Column(String(50))  # consultation, prescription, lab_report, imaging
    content = Column(Text)  # Main content of the record
    diagnosis = Column(String(500))
    medications = Column(JSON)  # List of medications
    metadata = Column(JSON)  # Additional metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="history")
    
    def __repr__(self):
        return f"<PatientHistory(id={self.id}, patient_id={self.patient_id}, type={self.record_type})>"

class MedicalRecord(Base):
    """Detailed medical records"""
    __tablename__ = "medical_records"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(100), ForeignKey("patients.patient_id"), nullable=False, index=True)
    record_type = Column(String(50))  # consultation, emergency, follow_up
    chief_complaint = Column(Text)
    symptoms = Column(JSON)  # List of symptoms
    diagnosis = Column(Text)
    treatment_plan = Column(Text)
    medications = Column(JSON)
    lab_results = Column(JSON)
    imaging_results = Column(JSON)
    doctor_notes = Column(Text)
    follow_up_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Blockchain reference
    blockchain_hash = Column(String(100))  # Hash stored on blockchain
    nft_token_id = Column(String(100))  # NFT token ID if minted
    
    # Relationships
    patient = relationship("Patient", back_populates="medical_records")
    
    def __repr__(self):
        return f"<MedicalRecord(id={self.id}, patient_id={self.patient_id})>"

class AgentLog(Base):
    """Agent activity logs"""
    __tablename__ = "agent_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(50), index=True)
    agent_name = Column(String(100))
    action = Column(String(100))
    message_type = Column(String(100))
    from_agent = Column(String(50))
    to_agent = Column(String(50))
    payload = Column(JSON)
    priority = Column(Integer)
    status = Column(String(50))  # success, error, pending
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AgentLog(id={self.id}, agent={self.agent_name}, action={self.action})>"

class TokenTransaction(Base):
    """Blockchain token transactions"""
    __tablename__ = "token_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(100), index=True)
    transaction_type = Column(String(50))  # reward, burn, transfer
    amount = Column(Float)
    reason = Column(String(500))
    tx_hash = Column(String(100))  # Blockchain transaction hash
    block_number = Column(Integer)
    status = Column(String(50))  # pending, confirmed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime)
    
    def __repr__(self):
        return f"<TokenTransaction(id={self.id}, patient={self.patient_id}, amount={self.amount})>"
