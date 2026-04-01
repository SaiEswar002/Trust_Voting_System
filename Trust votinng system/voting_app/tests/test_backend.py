import os
import sys

# Ensure backend module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.blockchain import Blockchain, Block
from backend.crypto_utils import encrypt_vote, tally_encrypted_votes, decrypt_tally, hash_fingerprint

def test_fingerprint_hashing():
    raw_1 = "fp1"
    raw_2 = "fp2"
    hash_1 = hash_fingerprint(raw_1)
    hash_2 = hash_fingerprint(raw_2)
    
    assert hash_1 != raw_1
    assert hash_1 != hash_2
    assert len(hash_1) == 64

def test_homomorphic_addition():
    v1_vec = [1, 0, 0] # Voted A
    v2_vec = [0, 1, 0] # Voted B
    v3_vec = [1, 0, 0] # Voted A
    
    enc_1 = encrypt_vote(v1_vec)
    enc_2 = encrypt_vote(v2_vec)
    enc_3 = encrypt_vote(v3_vec)
    
    tally = tally_encrypted_votes([enc_1, enc_2, enc_3])
    final_result = decrypt_tally(tally)
    
    # 2 for A, 1 for B, 0 for C
    assert final_result == [2, 1, 0]

def test_blockchain_consistency():
    chain = Blockchain()
    
    b1 = Block(1, {"vote": "mock"}, chain.last_block.hash)
    b1.hash = chain.proof_of_work(b1)
    
    assert chain.add_block(b1, b1.hash) == True
    assert len(chain.chain) == 2
    
    b2 = Block(2, {"vote": "mock2"}, b1.hash)
    b2.hash = chain.proof_of_work(b2)
    
    assert chain.add_block(b2, b2.hash) == True
    assert len(chain.chain) == 3
