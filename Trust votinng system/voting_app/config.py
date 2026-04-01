import os

class Config:
    # Election Metadata
    ELECTION_NAME = "National Cryptographic Test Election 2026"
    ELECTION_DATE = "November 3, 2026"
    
    # Flask Session
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-cryptographic-election-key')
    SESSION_TYPE = 'filesystem'
    
    # TODO: [DB Migration Checklist]
    # Move these credentials to the Database schema (e.g. `users` table) with hashed passwords
    # using werkzeug.security.generate_password_hash during the DB migration.
    WORKER_CREDENTIALS = {
        "officer1": "pin1234",
        "officer2": "pin5678"
    }
    
    ADMIN_CREDENTIALS = {
        "commission_admin": "master-pass-999"
    }

    # Used for simulating power cuts in local dev
    ALLOW_RESET = True
