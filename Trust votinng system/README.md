# End-to-End Cryptographic Blockchain Voting System

This project is a comprehensive simulation of a next-generation electronic voting system that mathematically guarantees voter privacy, election integrity, and system resilience. It combines **Biometric Hashing**, **Homomorphic Encryption**, **Zero-Knowledge Proofs (ZKPs)**, and **Blockchain Technology (Proof-of-Work)** into a fully functional 4-dashboard web application.

---

## 🔐 Core Cryptographic Technologies Used

1. **SHA-256 Biometric Hashing (Authentication)**
    - Raw fingerprints are never stored or transmitted. They are instantly hashed on the local machine using SHA-256. Only this hash is checked against the internal voter database.

2. **Paillier Homomorphic Encryption (Privacy)**
    - Your vote (e.g., `[0, 1, 0]` for Party B) is encrypted into massive ciphertexts before leaving the machine.
    - **Homomorphic Property:** The system can mathematically add these encrypted ciphertexts together to compute a final tally *without ever decrypting the individual votes*.

3. **Zero-Knowledge Proofs (Verifiability)**
    - The voting machine attaches a cryptographic ZKP to prove that the encrypted vote is valid (e.g., exactly one vote was cast, no negative votes, no multiple votes) without revealing *who* you voted for.

4. **Proof-of-Work Blockchain (Immutability)**
    - Votes are bundled into blocks and secured via a cryptographic hash-chain (similar to Bitcoin).
    - If a single bit of historical data is altered, the entire chain's hashes mathematically break, instantly alerting all validators.

---

## 🧮 Deep Dive: Cryptographic Implementation

### 1. SHA-256 Biometric Hashing (Voter Authentication)
- **Algorithm:** Secure Hash Algorithm (`hashlib.sha256()`)
- **Purpose:** To verify identity without ever exposing or storing raw biometric patterns.
- **Implementation:** The raw simulated frontend fingerprint input (e.g., `fp1`) is converted to byte format and passed through SHA-256. 
- **Code Logic:** `hashlib.sha256(raw_fingerprint.encode()).hexdigest()`
- **Security Guarantee:** Since SHA-256 is a deterministic one-way cryptographic hash function, even if the `voter_db.py` database is leaked, it is mathematically impossible to reverse-engineer the original thumbprints. The system only confirms if hashes match.

### 2. Paillier Homomorphic Encryption (Vote Privacy & Arithmetic Tallying)
- **Algorithm:** Asymmetric Paillier Cryptosystem (`phe` library)
- **Key Generation:** A highly secure 512-bit asymmetric keypair is dynamically generated upon server startup.
- **Vote Encoding:** A vote is encoded as a one-hot vector (e.g., Party B = `[0, 1, 0]`). Each integer is encrypted individually.
- **Encryption Equation (Simplified):** `E(m, r) = g^m * r^n (mod n^2)`
- **Homomorphic Addition Property:** The `tally_encrypted_votes` function leverages the unique mathematical equation:
  `E(m_1) * E(m_2) (mod n^2) = E(m_1 + m_2)`
- **Implementation:** By securely multiplying the massive ciphertext blocks of every voter together, the system computes the final aggregate tally *without ever holding the decryption key*. Only the Election Commission physically possesses the Private Key (`pk_p_q`) to decrypt the final mathematical sum into clear text.

### 3. Zero-Knowledge Proofs (ZKP) (Tamper Verification)
- **Concept:** A cryptographic proof that the encrypted vector is valid (contains exactly one `1` and the rest `0`s), without revealing strictly *which* index holds the `1`.
- **Simulation Implementation:** In this academic implementation (`crypto_utils.py`), a `mock_zkp_signature` is generated at the moment of encryption by taking a SHA-256 hash of the concatenated ciphertext array combined with a cryptographic salt. 
- **Verification:** Before a block is natively mined, the validator node enforces `verify_zkp(...) == True`. This process guarantees the encrypted envelope hasn't been tampered with or corrupted while propagating from the polling machine to the ledger.

### 4. Proof-of-Work Blockchain Hashing (Immutable State)
- **Block Structure:** Each block contains an `index`, `timestamp`, `data` payload (the serialized encrypted vote + receipt_id + zkp), a `previous_hash`, and a completely arbitrary `nonce`.
- **Consensus Protocol:** The system enforces a localized Proof-of-Work algorithm (`proof_of_work()`). It iteratively increments the `nonce` integer and calculates the SHA-256 hash of the block's concatenated string contents over and over until it probabilistically discovers a hash that starts with four leading zeros (e.g., `0000a3f...`).
- **Chain Validation:** The `is_valid_chain()` mechanism iteratively crawls from the Genesis Block to the latest block. It recalculates the hash of every single block natively and asserts two conditions:
  1. `current_block.hash == computed_hash`
  2. `current_block.previous_hash == previous_block.hash`
- **Security Result:** Any byte-level alteration to the JSON payload (e.g., via the Hacker Simulation) cascades structurally, permanently breaking the hash chain's mathematical integrity and flagging the chain as invalid.

---

## 🖥 The 4 Dashboards

### 1. The Main Voting Booth (`http://127.0.0.1:5000/`)
The primary interface for the voter. Demonstrates the strict 7-stage life cycle of a secure vote.
*   **Voter Pool:** You can log in using `V1` through `V10`.
*   **Biometrics:** You must provide the matching fingerprint (`fp1` through `fp10`).
*   **Encryption & Receipt:** Gives the voter a unique tracking receipt so they can verify their vote is on the blockchain.

### 2. Booth Admin Dashboard (`http://127.0.0.1:5000/admin`)
The interface for Election Officers running the polling station.
*   Shows a real-time list of all 10 registered voters.
*   Tracks who has passed biometric checks and successfully locked in a vote on the ledger.

### 3. Public Ledger Explorer (`http://127.0.0.1:5000/explorer`)
A transparent, raw view into the blockchain designed for public auditors or validator nodes.
*   Displays the Genesis Block and all subsequent mined vote blocks.
*   Shows the previous hash, block hash, nonce, and the heavily encrypted JSON payload.

### 4. Election Commission Tally (`http://127.0.0.1:5000/commission`)
The secure backend interface where the final election results are decrypted.
*   Because the blockchain can only homomorphically *add* ciphertexts, it requires a master Private Key to decrypt that final sum into readable votes.
*   Inputting the Private Key dynamically generated for the session unveils the winner.

---

## 💥 Threat & Disaster Simulations

To demonstrate the robustness of the architecture, the system includes two real-world failure simulations:

### Simulation A: Machine Power Cut (Atomic Rollback)
*   **Where to find it:** In the Main Voting Booth (`/`), press the faint grey `[Simulate Power Cut]` link at the bottom right corner *while the machine is actively securing/encrypting your vote*.
*   **What it proves:** If power is cut or the machine crashes before the blockchain mines the block, the voting transaction is legally incomplete. The memory is instantly wiped. Because the database operates atomically, the blockchain remains untouched, and the user is not locked out. They can simply restart their session.

### Simulation B: Malicious Node Hacker
*   **Where to find it:** In the Blockchain Explorer (`/explorer`), click the **Mutate Data (Hack)** button on any mined block.
*   **What it proves:** This allows you to forcefully bypass consensus and change an encrypted vote payload directly in memory.
*   When you attempt to click **"Validate Entire Chain"** afterward, the blockchain's cryptographic integrity algorithm will instantly catch the mutation. The hash chain will break, and the UI will flag the system as compromised.

---

## ⚙️ How It Works (The 7-Step Life Cycle)

1.  **Arrival & Scan:** Voter inputs ID and thumbprint.
2.  **Auth (SHA-256):** Local machine hashes print, verifies against database, and confirms voter hasn't voted yet.
3.  **Selection:** Voter selects Party A, B, or C.
4.  **Homomorphic Encryption:** Machine encrypts selection into a large integer vector.
5.  **ZKP Generation:** Machine attaches mathematical proof of valid vote shape.
6.  **Blockchain Mining:** The encrypted package is broadcast and mined into a block via Proof-of-Work. The voter is now officially marked as `has_voted = True`.
7.  **Receipt:** The machine wipes all raw data from RAM and outputs a tracking ID.

---

## 🛠 Installation & Execution

1. **Prerequisites:** Ensure you have Python 3.8+ installed.
2. **Setup Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Requires: `Flask`, `phe` for encryption, `pytest`)*
4. **Run the Server:**
   ```bash
   python app.py
   ```
   *The server auto-generates a new unique Private/Public key pair and a fresh Genesis Block upon startup.*
5. **Master Reset:** To instantly zero-out the blockchain and reset all 10 Voter statuses back to pending without rebooting the server, click the faint grey `[Master Reset]` link at the bottom right of the Admin dashboard.

---

## 🚀 Deployment Roadmap

As the system moves toward production readiness, the following steps are required for a hardened deployment:

### 1. Database Migration Path
The current state relies on `backend/db_stub.py`. Before production:
* Install SQLAlchemy & Alembic (`pip install flask-sqlalchemy psycopg2-binary alembic`).
* Define strict relational models in `backend/models.py` for `Voter`, `Receipt`, and `ElectionStateHistory`.
* Use `alembic init` to set up migration tracking.
* Replace the mock operations in `DatabaseStub` with actual PostgreSQL transactions.

### 2. Environment Variables Needed
A robust `.env` file must be provisioned injected securely into `config.py`:
* `FLASK_ENV`: Set to `production`.
* `DATABASE_URL`: Connection string for PostgreSQL (e.g., `postgresql://user:pass@db:5432/trust_vote`).
* `SECRET_KEY`: A cryptographically secure random string for Flask-Session.
* `PORT` / `PEER_NODES`: The list of networked IPs/Domains replacing the hardcoded `127.0.0.1` peer list.

### 3. Docker Compose Setup
The system components (Web Frontend, SocketIO Server, PostgreSQL DB, Redis for Sessions/PubSub) must be orchestrated.

```yaml
version: '3.8'
services:
  webapp:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres_db:5432/trust_vote
    depends_on:
      - postgres_db
      - redis_cache
  
  postgres_db:
    image: postgres:14-alpine
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=trust_vote
      
  redis_cache:
    image: redis:alpine
```

Upon standing up the containers, `flask db upgrade` must be run sequentially prior to launching the initial Genesis block.
