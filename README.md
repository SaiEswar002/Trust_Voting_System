# Trust Voting System

A cryptographically secured decentralized electronic voting platform demonstrating homomorphic encryption, zero-knowledge proofs, and blockchain consensus for auditable elections.

![Python](https://img.shields.io/badge/python-3.10-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

---

## What Problem Does This Solve?

Traditional electronic voting systems face a fundamental tension: they must simultaneously guarantee voter anonymity and provide public auditability. Centralized databases can be tampered with, trusted third parties introduce single points of failure, and most systems require voters to trust that their ballots are counted correctly without any way to verify.

This project demonstrates a cryptographic approach to resolving these conflicts. By combining **Paillier homomorphic encryption** with **zero-knowledge proofs** and a **proof-of-work blockchain**, the system allows votes to be publicly recorded and verified without ever decrypting individual ballots. Each vote exists on-chain as an encrypted vector, provably well-formed but computationally infeasible to decode. Only the final aggregate tally is decrypted—meaning no individual vote is ever exposed, even to system administrators.

Built as a BTech CSE DevOps specialization project at KL University, this implementation prioritizes educational clarity and architectural transparency. It simulates a peer-to-peer network using six Flask nodes, each maintaining a full copy of the blockchain and participating in consensus. While not production-ready in its current form, it demonstrates the cryptographic primitives and distributed architecture that underpin secure digital democracy.

---

## Architecture Overview

The system consists of six independent Flask nodes (ports 5001–5006) that form a simulated P2P network. Each node maintains its own blockchain replica, validates incoming blocks, and participates in mining. State synchronization happens through internal HTTP broadcasts—when any node mines a block or resets the chain, it propagates the update to all peers.

**For detailed architecture documentation, see [`ARCHITECTURE.md`](./ARCHITECTURE.md)**

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (User/Worker/Admin)                                │
│  ↓ HTTP/WebSocket                                           │
│  Flask Node (any of 5001-5006)                              │
│  ├─ Role-based routes (/user, /worker, /admin)             │
│  ├─ Blockchain module (PoW mining, chain validation)       │
│  ├─ Crypto module (Paillier, ZKP, SHA-256)                 │
│  └─ P2P sync (broadcasts to peers on state change)         │
└─────────────────────────────────────────────────────────────┘
```

---

## Cryptographic Stack

| Layer | Algorithm | What It Protects | Implementation |
|-------|-----------|------------------|----------------|
| **Identity** | SHA-256 biometric hashing | Voter anonymity—raw fingerprints never stored, only irreversible hashes | `crypto_module.hash_fingerprint()` |
| **Ballot Secrecy** | Paillier homomorphic encryption (512-bit) | Individual vote confidentiality—votes encrypted as one-hot vectors, never decrypted individually | `crypto_module.encrypt_vote()` |
| **Validity Proof** | Zero-knowledge proof (challenge-response) | Ballot integrity—proves each vote contains exactly one selection without revealing which | `crypto_module.generate_zkp()` |
| **Immutability** | Proof-of-work blockchain (SHA-256, difficulty 4) | Tamper evidence—computational cost to rewrite history, public audit trail | `blockchain.mine_block()` |

---

## Quick Start

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/trust-voting-system.git
cd trust-voting-system

# Install dependencies
pip install -r requirements.txt
```

### Running the Network

**Windows:**
```bash
start_network.bat
```

**Linux/macOS:**
```bash
chmod +x start_network.sh
./start_network.sh
```

This launches six Flask instances on ports 5001–5006. Access any node (e.g., `http://localhost:5001`) to interact with the system.

---

## Default Credentials

| Role | Username | Password | Capabilities |
|------|----------|----------|--------------|
| **User** (Voter) | `voter1` | `pass123` | Register fingerprint, cast vote, view receipt |
| **Worker** (Booth Officer) | `worker1` | `work123` | Verify voter eligibility, assist registration |
| **Admin** (Election Commission) | `admin` | `admin123` | Start/stop election, decrypt final tally, reset system |

All credentials are defined in `config.py`. **Do not use these in production.**

---

## Demo Walkthrough

### 1. Initialize the Election
- Login as **admin** on any node (e.g., `http://localhost:5001/admin`)
- Navigate to Admin Dashboard
- Click **"Start Election"** to transition from `REGISTRATION` → `ACTIVE`

### 2. Voter Registration
- Login as **voter1** at `/user`
- Submit biometric fingerprint (simulated as text input)
- System hashes fingerprint with SHA-256, stores hash in voter registry
- Voter is now eligible to cast ballot

### 3. Cast a Vote
- While election is `ACTIVE`, select a candidate
- Click **"Submit Vote"**
- Backend encrypts vote as Paillier ciphertext, generates ZKP
- Node mines a new block (PoW with 4 leading zeros)
- Block propagates to all peer nodes via broadcast

### 4. Receive Receipt
- After successful mining, voter receives SHA-256 receipt hash
- QR code generated for offline verification
- Receipt contains: `voter_hash`, `block_height`, `timestamp`, `node_id`

### 5. Close Election
- Admin clicks **"Close Election"** → state becomes `CLOSED`
- No new votes accepted; blockchain frozen

### 6. Decrypt Final Tally
- Admin navigates to **"Tally Results"**
- System performs homomorphic addition on all encrypted vote vectors
- Paillier private key decrypts **only the aggregate sum**, not individual votes
- Results displayed with per-candidate totals

---

## Project Structure

```
trust-voting-system/
├── app.py                    # Flask application entry point, route definitions
├── blockchain.py             # Block class, chain validation, PoW mining logic
├── crypto_module.py          # Paillier encryption, ZKP generation, SHA-256 hashing
├── config.py                 # Hardcoded credentials, node ports, difficulty params
├── network_sync.py           # P2P broadcast functions for block/reset propagation
├── requirements.txt          # Python dependencies (Flask, phe, qrcode, etc.)
├── start_network.bat         # Windows network launcher (6 nodes)
├── start_network.sh          # Linux/macOS network launcher
├── templates/
│   ├── user_dashboard.html  # Voter interface (register, vote, receipt)
│   ├── worker_dashboard.html # Booth officer interface
│   ├── admin_dashboard.html # Election commission controls
│   └── explorer.html        # Public blockchain viewer
├── static/
│   ├── css/
│   │   └── style.css        # Styling for all interfaces
│   └── js/
│       └── main.js          # WebSocket handlers, QR rendering, live updates
├── docs/
│   └── ARCHITECTURE.md      # Detailed crypto/consensus documentation
└── README.md                # This file
```

---

## Security Analysis

### What This System Demonstrates

✅ **Voter anonymity preserved**: Only biometric hashes are stored; raw fingerprints never touch the database.

✅ **Ballot secrecy maintained**: Individual votes remain encrypted on-chain indefinitely. Decryption only occurs on the final aggregate tally.

✅ **Vote validity provable**: ZKP cryptographically guarantees each ballot is well-formed (exactly one candidate selected) without revealing the choice.

✅ **Tamper-evident ledger**: PoW blockchain makes retroactive ballot stuffing computationally expensive. Any chain rewrite requires re-mining all subsequent blocks.

✅ **Public auditability**: Anyone can inspect the encrypted blockchain at `/explorer` and verify block hashes, timestamps, and proof-of-work.

### Known Limitations (Honest Assessment)

⚠️ **512-bit Paillier keypair**: Demonstration strength only. Production systems typically use 2048-bit or 3072-bit keys. Current implementation vulnerable to factorization attacks with sufficient computational resources.

⚠️ **Low PoW difficulty (4 leading zeros)**: Chosen for fast demo mining (~2–5 seconds per block). A real deployment would require higher difficulty to prevent chain manipulation.

⚠️ **In-memory state, no database persistence**: All voter registrations, blockchain data, and election state are held in Python dictionaries. Restarting a node loses its state. PostgreSQL migration is planned but not yet implemented.

⚠️ **Session credentials hardcoded**: `config.py` contains plaintext usernames and passwords. Production deployment requires environment variables, secure secret management, and hashed password storage.

⚠️ **Booth hardware trust assumption**: The system assumes the voting terminal itself is not compromised. Last-mile device security (tamper-evident hardware, secure boot, trusted execution environments) is out of scope for this prototype.

⚠️ **No Byzantine fault tolerance**: The P2P sync mechanism assumes honest nodes. A malicious node can attempt to broadcast invalid blocks, though other nodes will reject them during validation. Consensus is simple longest-chain, not BFT.

⚠️ **ZKP implementation is educational**: The zero-knowledge proof uses a simple challenge-response protocol adequate for demonstration. Production systems would require more robust ZKP frameworks (zk-SNARKs, Bulletproofs).

---

## Deployment Roadmap

### Phase 1: Database Persistence (Planned)
- Migrate in-memory state to PostgreSQL
- Implement SQLAlchemy ORM for voter registry, blockchain storage
- Add database migrations with Alembic
- Persistent node recovery after restart

### Phase 2: Production Hardening (Planned)
- Upgrade Paillier keypair to 2048-bit minimum
- Increase PoW difficulty based on network hashrate
- Environment variable injection for secrets (`.env` + `python-dotenv`)
- Argon2 password hashing for user credentials
- Rate limiting and CAPTCHA on registration endpoints

### Phase 3: Containerization (Planned)
- Dockerfile for each node
- Docker Compose orchestration for multi-node network
- Kubernetes manifests for cloud deployment
- Nginx reverse proxy with TLS termination

### Phase 4: Enhanced ZKP (Research)
- Evaluate zk-SNARK libraries (libsnark, bellman)
- Implement range proofs for ballot well-formedness
- Benchmark proof generation and verification times

---

## Contributing & Academic Use

This project was developed as a BTech CSE DevOps specialization demonstration at KL University. It is intended for **educational purposes** to illustrate cryptographic voting primitives and distributed consensus mechanisms.

**If you are a student or researcher:**
- Feel free to fork, modify, and extend this codebase
- Cite this repository if used in academic work
- Open issues for questions or discussions about the cryptographic design

**If you are considering production deployment:**
- **Do not deploy this system for real elections without extensive security review**
- Consult cryptographers and election security experts
- Address all items in the "Known Limitations" section
- Conduct third-party security audits and penetration testing

**Pull requests welcome** for bug fixes, documentation improvements, or feature enhancements that maintain educational clarity.

---

## License

MIT License. See `LICENSE` file for details.

---

## Acknowledgments

- **KL University** — BTech CSE DevOps program support
- **Paillier cryptosystem** — Homomorphic encryption scheme by Pascal Paillier
- **python-phe library** — Efficient Paillier implementation
- **Flask & SocketIO** — Web framework and real-time communication

---

## Contact

**Developer:** E. Sai Eswar  
**Institution:** KL University, BTech CSE (DevOps Specialization)  
**Project Type:** Hackathon / Academic Demonstration  
For questions about the cryptographic implementation, see [`ARCHITECTURE.md`](./ARCHITECTURE.md). For general inquiries, open an issue in this repository.
