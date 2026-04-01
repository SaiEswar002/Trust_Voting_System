import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Election Metadata
    ELECTION_NAME = "National Cryptographic Test Election 2026"
    ELECTION_DATE = "November 3, 2026"
    
    # Flask Session
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(BASE_DIR, 'flask_session')
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    
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
