from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from utils.logger import setup_logger

logger = setup_logger(__name__)

class MedicationAgent(BaseAgent):
    """Medication adherence tracking and reminder agent"""
    
    def __init__(self, agent_id: str, name: str):
        super().__init__(agent_id, name, "medication_adherence")
        self.active_schedules = {}  # patient_id -> medication schedule
        self.adherence_records = {}  # patient_id -> adherence data
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process medication tracking operations"""
        self.set_status("processing")
        
        try:
            action = input_data.get("action", "track")
            patient_id = input_data["patient_id"]
            
            if action == "start_tracking":
                medications = input_data["medications"]
                result = await self._start_tracking(patient_id, medications)
                return result
            
            elif action == "log_dose":
                medication_name = input_data["medication_name"]
                taken = input_data.get("taken", True)
                result = await self._log_dose(patient_id, medication_name, taken)
                return result
            
            elif action == "get_adherence":
                result = await self._get_adherence_report(patient_id)
                return result
            
            elif action == "check_reminders":
                result = await self._check_reminders(patient_id)
                return result
            
            self.set_status("idle")
            
        except Exception as e:
            logger.error(f"❌ Medication Agent error: {str(e)}")
            self.set_status("error")
            return {"error": str(e)}
    
    async def receive_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle medication tracking requests"""
        msg_type = message['type']
        payload = message['payload']
        
        if msg_type == "START_MEDICATION_TRACKING":
            logger.info(f"💊 Starting medication tracking")
            return await self.process({**payload, "action": "start_tracking"})
        
        elif msg_type == "LOG_MEDICATION_TAKEN":
            return await self.process({**payload, "action": "log_dose"})
        
        elif msg_type == "CHECK_ADHERENCE":
            return await self.process({**payload, "action": "get_adherence"})
        
        return None
    
    async def _start_tracking(self, patient_id: str, medications: List[Dict]) -> Dict:
        """Start tracking medication schedule"""
        logger.info(f"📅 Setting up medication schedule for {patient_id}")
        
        schedule = []
        
        for med in medications:
            med_schedule = {
                "name": med["name"],
                "dosage": med["dosage"],
                "frequency": med["frequency"],
                "times": self._parse_frequency(med["frequency"]),
                "duration_days": self._parse_duration(med.get("duration", "7 days")),
                "start_date": datetime.now().isoformat(),
                "instructions": med.get("instructions", "")
            }
            schedule.append(med_schedule)
        
        self.active_schedules[patient_id] = schedule
        self.adherence_records[patient_id] = {
            "total_doses": 0,
            "taken_doses": 0,
            "missed_doses": 0,
            "streak_days": 0,
            "last_taken": None
        }
        
        logger.info(f"✅ Tracking {len(schedule)} medications")
        
        return {
            "success": True,
            "medications_tracked": len(schedule),
            "schedule": schedule
        }
    
    async def _log_dose(self, patient_id: str, medication_name: str, taken: bool) -> Dict:
        """Log medication dose taken/missed"""
        logger.info(f"📝 Logging dose: {medication_name} - {'Taken' if taken else 'Missed'}")
        
        if patient_id not in self.adherence_records:
            self.adherence_records[patient_id] = {
                "total_doses": 0,
                "taken_doses": 0,
                "missed_doses": 0,
                "streak_days": 0,
                "last_taken": None
            }
        
        record = self.adherence_records[patient_id]
        record["total_doses"] += 1
        
        if taken:
            record["taken_doses"] += 1
            record["last_taken"] = datetime.now().isoformat()
            
            # Update streak
            if record.get("last_taken_date") == datetime.now().date():
                pass  # Same day, don't increment
            else:
                record["streak_days"] += 1
            
            record["last_taken_date"] = datetime.now().date()
            
            # Calculate adherence percentage
            adherence_pct = (record["taken_doses"] / record["total_doses"]) * 100
            
            # Reward for good adherence
            if adherence_pct >= 90 and record["total_doses"] >= 7:
                await self._reward_adherence(patient_id, record["streak_days"])
        else:
            record["missed_doses"] += 1
            record["streak_days"] = 0  # Reset streak
        
        return {
            "logged": True,
            "medication": medication_name,
            "taken": taken,
            "adherence_percentage": (record["taken_doses"] / record["total_doses"]) * 100 if record["total_doses"] > 0 else 0,
            "streak_days": record["streak_days"]
        }
    
    async def _get_adherence_report(self, patient_id: str) -> Dict:
        """Generate adherence report"""
        logger.info(f"📊 Generating adherence report for {patient_id}")
        
        record = self.adherence_records.get(patient_id, {})
        schedule = self.active_schedules.get(patient_id, [])
        
        adherence_pct = (record.get("taken_doses", 0) / record.get("total_doses", 1)) * 100
        
        # Determine adherence level
        if adherence_pct >= 95:
            level = "excellent"
            message = "🎉 Outstanding adherence! Keep it up!"
        elif adherence_pct >= 80:
            level = "good"
            message = "✅ Good adherence. Try to not miss doses."
        elif adherence_pct >= 60:
            level = "fair"
            message = "⚠️ Fair adherence. Please try to be more consistent."
        else:
            level = "poor"
            message = "❌ Low adherence. This may affect your recovery. Please follow the schedule."
        
        return {
            "patient_id": patient_id,
            "adherence_percentage": round(adherence_pct, 1),
            "level": level,
            "message": message,
            "total_doses": record.get("total_doses", 0),
            "taken_doses": record.get("taken_doses", 0),
            "missed_doses": record.get("missed_doses", 0),
            "current_streak_days": record.get("streak_days", 0),
            "medications_tracked": len(schedule)
        }
    
    async def _check_reminders(self, patient_id: str) -> Dict:
        """Check if any medication reminders are due"""
        logger.info(f"⏰ Checking reminders for {patient_id}")
        
        schedule = self.active_schedules.get(patient_id, [])
        current_time = datetime.now()
        
        due_reminders = []
        
        for med in schedule:
            for reminder_time in med.get("times", []):
                # Check if reminder is within next 30 minutes
                reminder_dt = datetime.strptime(reminder_time, "%H:%M").replace(
                    year=current_time.year,
                    month=current_time.month,
                    day=current_time.day
                )
                
                time_diff = (reminder_dt - current_time).total_seconds() / 60
                
                if 0 <= time_diff <= 30:
                    due_reminders.append({
                        "medication": med["name"],
                        "dosage": med["dosage"],
                        "time": reminder_time,
                        "instructions": med["instructions"]
                    })
        
        return {
            "reminders_due": len(due_reminders),
            "reminders": due_reminders
        }
    
    async def _reward_adherence(self, patient_id: str, streak_days: int):
        """Reward patient for good adherence"""
        logger.info(f"🎁 Rewarding adherence: {streak_days} day streak")
        
        # Calculate reward based on streak
        base_reward = 10
        streak_bonus = min(streak_days * 2, 50)  # Max 50 bonus
        total_reward = base_reward + streak_bonus
        
        # Send to blockchain agent
        await self.send_message(
            "chain-1",
            "REWARD_ADHERENCE",
            {
                "patient_id": patient_id,
                "amount": total_reward,
                "reason": f"{streak_days}-day adherence streak"
            },
            priority=3
        )
    
    def _parse_frequency(self, frequency_str: str) -> List[str]:
        """Parse frequency string into times"""
        freq_lower = frequency_str.lower()
        
        if "once daily" in freq_lower or "1 time" in freq_lower:
            return ["09:00"]
        elif "twice daily" in freq_lower or "2 times" in freq_lower:
            return ["09:00", "21:00"]
        elif "three times" in freq_lower or "3 times" in freq_lower:
            return ["09:00", "15:00", "21:00"]
        elif "every 6 hours" in freq_lower:
            return ["06:00", "12:00", "18:00", "00:00"]
        elif "every 8 hours" in freq_lower:
            return ["08:00", "16:00", "00:00"]
        else:
            return ["09:00"]  # Default
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string into days"""
        import re
        
        match = re.search(r'(\d+)', duration_str)
        if match:
            days = int(match.group(1))
            
            if "week" in duration_str.lower():
                return days * 7
            elif "month" in duration_str.lower():
                return days * 30
            else:
                return days
        
        return 7  # Default 7 days
