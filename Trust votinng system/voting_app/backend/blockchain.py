import hashlib
import json
import time

class Block:
    def __init__(self, index, data, previous_hash, nonce=0):
        self.index = index
        self.timestamp = time.time()
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, list(), "0", 0)
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):
        previous_hash = self.last_block.hash
        if previous_hash != block.previous_hash:
            return False
        if not self.is_valid_proof(block, proof):
            return False
        block.hash = proof
        self.chain.append(block)
        return True

    def is_valid_proof(self, block, block_hash):
        # A simple proof of work logic for demonstration purposes
        return (block_hash.startswith('0' * 2) and
                block_hash == block.compute_hash())

    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * 2):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def is_valid_chain(self):
        # Starts at 1, skipping genesis
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Check if block data has been tampered with
            if current_block.hash != current_block.compute_hash():
                return {"is_valid": False, "broken_block": i, "reason": f"Block #{i} data was mutated — stored hash no longer matches computed hash."}
            # Check if the cryptographic link is broken
            if current_block.previous_hash != previous_block.hash:
                return {"is_valid": False, "broken_block": i, "reason": f"Block #{i} previous_hash link is broken — it does not match Block #{i-1}'s hash."}
        return {"is_valid": True, "broken_block": None, "reason": "All blocks are intact."}
