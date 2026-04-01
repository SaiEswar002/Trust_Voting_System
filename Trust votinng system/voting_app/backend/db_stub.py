import json
import os
from .voter_db import MOCK_VOTERS

class DatabaseStub:
    """
    Temporary in-memory stub. All methods mirror the interface
    that a real SQLAlchemy/PostgreSQL implementation will expose.
    Replace this class body with real DB calls during DB migration.
    
    # DB MIGRATION CHECKLIST
    # 1. pip install flask-sqlalchemy psycopg2-binary alembic
    # 2. Define models in backend/models.py (Voter, Receipt, ElectionEvent)
    # 3. Replace DatabaseStub methods with SQLAlchemy session calls
    # 4. Run alembic init + create initial migration
    # 5. Set DATABASE_URL in config.py / environment variable
    """
    
    def __init__(self):
        # Local state populated from voter_db.py MOCK_VOTERS
        self.voters = MOCK_VOTERS.copy()
        
        # In-memory dict for receipts
        # TODO: Migrate receipts dict to SQLite/PostgreSQL table:
        # receipts(receipt_id, voter_id, block_index, block_hash, checksum, timestamp)
        self.receipts = {}
        
        # In-memory state history
        self.election_history = []
        
    def get_voter(self, voter_id: str) -> dict | None:
        return self.voters.get(voter_id)
        
    def mark_voted(self, voter_id: str) -> bool:
        if voter_id in self.voters:
            self.voters[voter_id]["has_voted"] = True
            return True
        return False
        
    def get_all_voters(self) -> list[dict]:
        return [{"voter_id": k, **v} for k, v in self.voters.items()]
        
    def save_receipt(self, receipt: dict) -> bool:
        self.receipts[receipt['receipt_id']] = receipt
        return True
        
    def get_receipt(self, receipt_id: str) -> dict | None:
        return self.receipts.get(receipt_id)

    def save_election_state(self, state: str, changed_by: str, timestamp: str) -> bool:
        self.election_history.append({
            "state": state,
            "changed_by": changed_by,
            "timestamp": timestamp
        })
        return True
        
    def get_election_state_history(self) -> list[dict]:
        return self.election_history

    def reset(self):
        """Full data wipe in the DatabaseStub."""
        self.voters = MOCK_VOTERS.copy()
        self.receipts = {}
        self.election_history = []
        return True

# Singleton instance exported for use everywhere
db = DatabaseStub()
