from .crypto_utils import hash_fingerprint

def get_initial_voters():
    voters = {}
    # 6 booths, 10 voters each
    for booth in range(1, 7):
        for v in range(1, 11):
            vid = f"B{booth}_V{v}"
            fprint = f"b{booth}fp{v}"
            voters[vid] = {
                "fingerprint_hash": hash_fingerprint(fprint),
                "has_voted": False,
                "assigned_booth": booth
            }
    return voters

# Mock internal database linking voter IDs to biometric hashes and precinct booths
MOCK_VOTERS = get_initial_voters()

class VoterAPI:
    @staticmethod
    def get_voter(voter_id):
        return MOCK_VOTERS.get(voter_id)
        
    @staticmethod
    def mark_as_voted(voter_id):
        if voter_id in MOCK_VOTERS:
            MOCK_VOTERS[voter_id]["has_voted"] = True

    @staticmethod
    def reset_voters():
        global MOCK_VOTERS
        MOCK_VOTERS = get_initial_voters()
