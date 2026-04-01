import hashlib
import json
import os
import uuid
import time
from phe import paillier

# Instead of random key generation per boot, nodes securely load a shared master 
# homomorphic key file. In a real system, the Central Authority distributes the Public Key
# and securely holds the Private Key. Here we share keys to enable 6 local peer nodes.
KEY_FILE = os.path.join(os.path.dirname(__file__), 'shared_keys.json')

if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'r') as f:
        kd = json.load(f)
        n = int(kd['public_key']['n'])
        p = int(kd['private_key']['p'])
        q = int(kd['private_key']['q'])
        ELECTION_PUB_KEY = paillier.PaillierPublicKey(n=n)
        ELECTION_PRIV_KEY = paillier.PaillierPrivateKey(public_key=ELECTION_PUB_KEY, p=p, q=q)
else:
    ELECTION_PUB_KEY, ELECTION_PRIV_KEY = paillier.generate_paillier_keypair(n_length=512)
    with open(KEY_FILE, 'w') as f:
        json.dump({
            "public_key": {"n": str(ELECTION_PUB_KEY.n)},
            "private_key": {"p": str(ELECTION_PRIV_KEY.p), "q": str(ELECTION_PRIV_KEY.q)}
        }, f)


def hash_fingerprint(raw_data: str) -> str:
    """Consumes raw fingerprint string, returns SHA-256 hash."""
    return hashlib.sha256(raw_data.encode('utf-8')).hexdigest()

def encrypt_fingerprint(raw_data: str) -> dict:
    """Encrypts the hash of the fingerprint using Paillier."""
    hashed = hash_fingerprint(raw_data)
    hash_int = int(hashed, 16)
    encrypted = ELECTION_PUB_KEY.encrypt(hash_int)
    return serialize_encrypted_fingerprint(encrypted)

def serialize_encrypted_fingerprint(enc) -> dict:
    """Serializes phe EncryptedNumber to dict."""
    return {"ciphertext": str(enc.ciphertext()), "exponent": enc.exponent}

def deserialize_encrypted_fingerprint(d: dict):
    """Reconstructs the phe EncryptedNumber from dict."""
    return paillier.EncryptedNumber(ELECTION_PUB_KEY, int(d["ciphertext"]), int(d["exponent"]))

def decrypt_fingerprint(enc) -> int:
    """Decrypts the encrypted fingerprint hash."""
    return ELECTION_PRIV_KEY.decrypt(enc)

def generate_receipt_id(voter_id: str) -> str:
    """Generates an anonymous receipt ID based on voter ID and exact timestamp."""
    timestamp = str(time.time())
    raw = f"{voter_id}_{timestamp}_{uuid.uuid4()}"
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def encrypt_vote(vote_vector: list) -> list:
    """Encrypts each value of the vote vector [0,1,0] into Paillier ciphertext."""
    encrypted_vector = [ELECTION_PUB_KEY.encrypt(val) for val in vote_vector]
    # In a real scenario, this memory must be wiped carefully.
    return encrypted_vector

def generate_zkp(encrypted_vote: list) -> dict:
    """
    Mock Zero Knowledge Proof generation.
    In reality, demonstrates the encrypted vector contains exactly one '1' and remaining '0's.
    """
    return {
        "proof_type": "One-out-of-N",
        "valid": True,
        "signature": hashlib.sha256(str(uuid.uuid4()).encode('utf-8')).hexdigest()
    }

def verify_zkp(zkp: dict) -> bool:
    """Verifies the mock ZKP."""
    return zkp.get("valid", False)

def tally_encrypted_votes(encrypted_votes_list: list) -> list:
    """
    Takes a list of encrypted vote vectors and homomorphically adds them.
    E(A) + E(B) = E(A+B)
    """
    if not encrypted_votes_list:
        return []
    
    num_candidates = len(encrypted_votes_list[0])
    # Initialize with Encrypted(0)
    running_totals = [ELECTION_PUB_KEY.encrypt(0) for _ in range(num_candidates)]
    
    for enc_vote in encrypted_votes_list:
        for i in range(num_candidates):
            running_totals[i] = running_totals[i] + enc_vote[i]
            
    return running_totals

def decrypt_tally(running_totals: list) -> list:
    """The Election Commission finally decrypts the combined totals using private key."""
    return [ELECTION_PRIV_KEY.decrypt(total) for total in running_totals]

def serialize_encrypted_vote(enc_vote_vector) -> list:
    """Serializes phe EncryptedNumber objects to dicts for the blockchain payload/database storage."""
    return [{"ciphertext": str(ev.ciphertext()), "exponent": ev.exponent} for ev in enc_vote_vector]

def deserialize_encrypted_vote(dict_vector: list) -> list:
    """Reconstructs the phe EncryptedNumber objects from stored ciphertext dicts."""
    return [paillier.EncryptedNumber(ELECTION_PUB_KEY, int(val["ciphertext"]), int(val["exponent"])) for val in dict_vector]
