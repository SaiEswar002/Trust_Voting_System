import json
import os
from datetime import datetime
from .db_stub import db

class ElectionStateError(Exception):
    pass

class ElectionStateManager:
    STATES = ['REGISTRATION', 'ACTIVE', 'CLOSED', 'TALLIED']
    # File at the root of project (one level up from backend/)
    STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'election_state.json')

    @classmethod
    def get_state(cls) -> str:
        if not os.path.exists(cls.STATE_FILE):
            cls._write_state('REGISTRATION')
            # Initialize history
            timestamp = datetime.utcnow().isoformat()
            db.save_election_state('REGISTRATION', 'system', timestamp)
            return 'REGISTRATION'
            
        with open(cls.STATE_FILE, 'r') as f:
            try:
                data = json.load(f)
                return data.get('current_state', 'REGISTRATION')
            except json.JSONDecodeError:
                return 'REGISTRATION'

    @classmethod
    def _write_state(cls, state: str):
        with open(cls.STATE_FILE, 'w') as f:
            json.dump({'current_state': state}, f)

    @classmethod
    def transition_to(cls, new_state: str, admin_username: str) -> bool:
        current_state = cls.get_state()
        
        valid_transitions = {
            'REGISTRATION': 'ACTIVE',
            'ACTIVE': 'CLOSED',
            'CLOSED': 'TALLIED'
        }
        
        if valid_transitions.get(current_state) != new_state:
            raise ElectionStateError(f"Invalid transition from {current_state} to {new_state}")
            
        cls._write_state(new_state)
        # Log to "database" history stub
        timestamp = datetime.utcnow().isoformat()
        db.save_election_state(new_state, admin_username, timestamp)
        return True

    @classmethod
    def get_state_history(cls) -> list[dict]:
        return db.get_election_state_history()

    @classmethod
    def reset(cls) -> bool:
        """Deletes the state file and clears DatabaseStub."""
        if os.path.exists(cls.STATE_FILE):
            os.remove(cls.STATE_FILE)
        return db.reset()
