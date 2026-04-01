import os
import sys
import threading
import requests
import hashlib
import json
import base64
from io import BytesIO
from functools import wraps
from datetime import datetime

import qrcode
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_socketio import SocketIO
from flask_session import Session

# Ensure backend module can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from backend.blockchain import Blockchain, Block
import backend.crypto_utils as crypto
from backend.db_stub import db
from backend.election_state import ElectionStateManager, ElectionStateError

# Initialization
PORT = 5000
BOOTH_ID = 1

if len(sys.argv) >= 2:
    PORT = int(sys.argv[1])
if len(sys.argv) >= 3:
    BOOTH_ID = int(sys.argv[2])

PEER_NODES = [5001, 5002, 5003, 5004, 5005, 5006]

app = Flask(__name__)
app.config.from_object(Config)
Session(app)
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

election_chain = Blockchain()

# --- Context Processor ---
@app.context_processor
def inject_globals():
    return {
        'current_node_port': PORT,
        'current_node_label': BOOTH_ID,
        'election_state': ElectionStateManager.get_state(),
        'chain_length': len(election_chain.chain),
        'election_name': Config.ELECTION_NAME,
        'election_date': Config.ELECTION_DATE
    }

# --- Role Decorator ---
def require_role(roles):
    """Restricts route access based on session role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session:
                flash("Authentication required to access this portal.", "warning")
                return redirect(url_for('login_page'))
            if session['role'] not in roles:
                flash("Insufficient clearance level for this action. Access Denied.", "error")
                return redirect(url_for('login_page'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Page Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'GET':
        return render_template('login.html')
        
    role = request.form.get('role')
    
    if role == 'user':
        voter_id = request.form.get('voter_id')
        fingerprint_hash = request.form.get('fingerprint_hash')
        voter = db.get_voter(voter_id)
        
        # Fingerprint arrives pre-hashed (SHA-256 from browser) — compare directly
        if voter and voter['fingerprint_hash'] == fingerprint_hash:
            session['role'] = 'user'
            session['username'] = voter_id
            flash("Voter Authenticated. Proceed to Booth.", "success")
            return redirect(url_for('serve_index'))
        else:
            flash("Biometric verification failed or Voter ID not found.", "error")
            return redirect(url_for('login_page'))
            
    elif role == 'worker':
        username = request.form.get('username')
        password = request.form.get('password')
        if Config.WORKER_CREDENTIALS.get(username) == password:
            session['role'] = 'worker'
            session['username'] = username
            flash(f"Officer {username} securely logged in.", "success")
            return redirect(url_for('serve_admin'))
        else:
            flash("Invalid Officer credentials.", "error")
            return redirect(url_for('login_page'))
            
    elif role == 'admin':
        username = request.form.get('username')
        password = request.form.get('password')
        if Config.ADMIN_CREDENTIALS.get(username) == password:
            session['role'] = 'admin'
            session['username'] = username
            flash("Election Commission Master Access Granted.", "success")
            return redirect(url_for('serve_admin'))
        else:
            flash("Invalid Commission credentials.", "error")
            return redirect(url_for('login_page'))

    return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Successfully logged out of the network.", "success")
    return redirect(url_for('login_page'))

@app.route('/')
@require_role(['user'])
def serve_index():
    return render_template('booth.html')

@app.route('/admin')
@require_role(['worker', 'admin'])
def serve_admin():
    voters_raw = db.get_all_voters()
    voters = []
    for v in voters_raw:
        if v["assigned_booth"] == BOOTH_ID:
            v_hash = hashlib.sha256(str(v["voter_id"]).encode('utf-8')).hexdigest()
            voters.append({
                "voter_id": v["voter_id"],
                "voter_hash": v_hash,
                "has_voted": v["has_voted"],
                "fingerprint_hash": v["fingerprint_hash"]
            })
    return render_template('admin.html', voters=voters)

@app.route('/explorer')
@require_role(['worker', 'admin'])
def serve_explorer():
    chain_data = [b.__dict__ for b in election_chain.chain]
    return render_template('explorer.html', chain=chain_data)

@app.route('/commission')
@require_role(['admin'])
def serve_commission():
    return render_template('commission.html')

@app.route('/network-status')
@require_role(['admin'])
def serve_network_status():
    results = []
    reference_length = len(election_chain.chain)
    consensus_healthy = True
    
    for peer in PEER_NODES:
        if peer == PORT:
            results.append({"id": BOOTH_ID, "port": PORT, "status": "Online", "chain_length": reference_length})
        else:
            try:
                r = requests.get(f"http://127.0.0.1:{peer}/api/blockchain", timeout=1)
                data = r.json()
                if data['length'] != reference_length:
                    consensus_healthy = False
                results.append({"id": peer - 5000, "port": peer, "status": "Online", "chain_length": data['length']})
            except:
                results.append({"id": peer - 5000, "port": peer, "status": "Offline", "chain_length": 0})

    return render_template('network_status.html', nodes=results, consensus_healthy=consensus_healthy)

@app.route('/verify')
def serve_verify():
    receipt_id = request.args.get('receipt_id')
    return render_template('verify.html')

# --- CORE LOGIC API ---

@app.route('/authenticate', methods=['POST'])
def authenticate():
    # Only called from frontend AJAX during booth Phase 1
    if session.get('role') != 'user':
        return jsonify({"status": "error", "message": "Portal session expired."}), 401
        
    data = request.json
    voter_id = data.get('voter_id')
    input_hash = data.get('fingerprint_hash')

    if not voter_id or not input_hash:
        return jsonify({"status": "error", "message": "Missing credentials"}), 400

    voter_record = db.get_voter(voter_id)
    if not voter_record:
        return jsonify({"status": "error", "message": "Voter ID not found in registry"}), 404

    if voter_record["has_voted"]:
        return jsonify({"status": "error", "message": "Voter has already cast a vote (duplicate voting rejected)"}), 403

    if voter_record["assigned_booth"] != BOOTH_ID:
        return jsonify({"status": "error", "message": f"Access Denied: Registered at Booth {voter_record['assigned_booth']}!"}), 403

    # Fingerprint arrives pre-hashed (SHA-256 from browser) — compare directly
    if input_hash != voter_record["fingerprint_hash"]:
        return jsonify({"status": "error", "message": "Biometric authentication failed"}), 401
        
    if ElectionStateManager.get_state() != 'ACTIVE':
        return jsonify({"status": "error", "message": "Voting is not currently ACTIVE."}), 403

    return jsonify({"status": "success", "message": "Authentication successful. Proceed to private booth."}), 200

@app.route('/vote', methods=['POST'])
def cast_vote():
    if session.get('role') != 'user':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    if ElectionStateManager.get_state() != 'ACTIVE':
        return jsonify({"status": "error", "message": "Cannot cast votes unless Election State is ACTIVE."}), 403

    data = request.json
    voter_id = data.get('voter_id')
    vote_vector = data.get('vote_vector')
    fingerprint_hash = data.get('fingerprint_hash')
    
    voter_record = db.get_voter(voter_id)
    # Fingerprint arrives pre-hashed (SHA-256 from browser) — compare directly
    if not voter_record or fingerprint_hash != voter_record["fingerprint_hash"]:
        return jsonify({"status": "error", "message": "Authentication failed"}), 401

    if voter_record["has_voted"]:
        return jsonify({"status": "error", "message": "User has already voted."}), 403

    # Encrypt
    encrypted_vote_objs = crypto.encrypt_vote(vote_vector)
    serialized_enc_vote = crypto.serialize_encrypted_vote(encrypted_vote_objs)
    receipt_id = crypto.generate_receipt_id(voter_id)
    zkp = crypto.generate_zkp(encrypted_vote_objs)

    vote_payload = {
        "receipt_id": receipt_id,
        "encrypted_vote": serialized_enc_vote,
        "zkp": zkp
    }

    if not crypto.verify_zkp(zkp):
        return jsonify({"status": "error", "message": "ZKP Validation failed."}), 400

    # Add to chain
    last_block = election_chain.last_block
    new_block = Block(index=last_block.index + 1, data=vote_payload, previous_hash=last_block.hash)
    proof = election_chain.proof_of_work(new_block)
    election_chain.add_block(new_block, proof)

    # State mutations
    db.mark_voted(voter_id)
    
    # Generate receipt metadata
    computed_checksum = hashlib.sha256(f"{receipt_id}{new_block.hash}{voter_id}".encode()).hexdigest()
    receipt_metadata = {
        "receipt_id": receipt_id,
        "voter_id": voter_id,
        "block_index": new_block.index,
        "block_hash": new_block.hash,
        "timestamp": datetime.utcnow().isoformat(),
        "checksum": computed_checksum
    }
    db.save_receipt(receipt_metadata)

    # Generate QR Code image base64
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(json.dumps(receipt_metadata))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_b64 = "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()

    # Emit WebSockets
    socketio.emit('new_block', {
        'block_index': new_block.index,
        'voter_id_hash_prefix': base64.b64encode(hashlib.sha256(voter_id.encode()).digest()).decode()[:8],
        'nonce': new_block.nonce,
        'block_hash_preview': new_block.hash[:16],
        'timestamp': new_block.timestamp
    })
    
    socketio.emit('voter_status_change', {
        'voter_id': voter_id,
        'new_status': True
    })

    # Broadcast to P2P peers (daemon thread so it never blocks server shutdown)
    def broadcast_block(blk_dict):
        for peer_port in PEER_NODES:
            if peer_port != PORT:
                try:
                    requests.post(f"http://127.0.0.1:{peer_port}/internal/sync-reset", json=blk_dict, timeout=0.5)
                except Exception:
                    pass  # Offline peers are silently skipped
    
    blk_payload = dict(new_block.__dict__)
    t = threading.Thread(target=broadcast_block, args=(blk_payload,), daemon=True)
    t.start()

    return jsonify({
        "status": "success",
        "message": "Vote secured on blockchain.",
        "receipt_id": receipt_id,
        "qr_image": qr_b64
    }), 200

# --- SOCKETIO ACTIONS ---

@socketio.on('request_tally')
def handle_tally(data):
    if session.get('role') != 'admin':
        return
    if ElectionStateManager.get_state() not in ['CLOSED', 'TALLIED']:
        socketio.emit('tally_response', {"status": "error", "message": "Election must be CLOSED before computing final tally."})
        return
    provided_key = data.get('private_key')
    actual_key = f"pk_{crypto.ELECTION_PRIV_KEY.p}_{crypto.ELECTION_PRIV_KEY.q}"
    if provided_key != actual_key:
        socketio.emit('tally_response', {"status": "error", "message": "Access Denied: Invalid Master Private Key."})
        return
    all_encrypted_votes = []
    for block in election_chain.chain[1:]:
        payload = block.data
        if isinstance(payload, dict) and "encrypted_vote" in payload:
            try:
                reconstructed_enc = crypto.deserialize_encrypted_vote(payload["encrypted_vote"])
                all_encrypted_votes.append(reconstructed_enc)
            except Exception:
                continue
    if not all_encrypted_votes:
         socketio.emit('tally_response', {"status": "success", "results": [0, 0, 0], "message": "No valid votes found on chain."})
         return
    tally_encrypted = crypto.tally_encrypted_votes(all_encrypted_votes)
    final_tally = crypto.decrypt_tally(tally_encrypted)
    socketio.emit('tally_response', {"status": "success", "results": final_tally})

@socketio.on('request_transition')
def handle_transition(data):
    if session.get('role') != 'admin':
        return
    new_state = data.get('new_state')
    admin_user = session.get('username')
    try:
        ElectionStateManager.transition_to(new_state, admin_user)
        socketio.emit('election_state_change', {'new_state': new_state, 'changed_by': admin_user})
        socketio.emit('transition_response', {"status": "success"})
    except ElectionStateError as e:
        socketio.emit('transition_response', {"status": "error", "message": str(e)})

@socketio.on('request_hack')
def handle_hack(data):
    if session.get('role') != 'admin':
        return
    block_index = data.get('block_index')
    new_data = data.get('new_data')
    if block_index > 0 and block_index < len(election_chain.chain):
        election_chain.chain[block_index].data = new_data
        socketio.emit('hack_response', {"status": "success"})
    else:
        socketio.emit('hack_response', {"status": "error"})

@socketio.on('request_validation')
def handle_validation():
    if session.get('role') not in ['worker', 'admin']:
        return
    result = election_chain.is_valid_chain()
    socketio.emit('validation_response', {"status": "success", "is_valid": result["is_valid"], "broken_block": result["broken_block"], "reason": result["reason"]})

@socketio.on('request_private_key')
def handle_private_key():
    if session.get('role') != 'admin':
        return
    p_key_string = f"pk_{crypto.ELECTION_PRIV_KEY.p}_{crypto.ELECTION_PRIV_KEY.q}"
    socketio.emit('private_key_response', {"private_key": p_key_string})

@app.route('/admin/master-reset', methods=['POST'])
@require_role(['admin'])
def reset_election():
    global election_chain
    try:
        ElectionStateManager.reset()
        election_chain = Blockchain()
        socketio.emit('election_reset', {'status': 'success'})
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/internal/sync-reset', methods=['POST'])
def receive_block():
    block_data = request.json
    if block_data['index'] > election_chain.last_block.index:
        new_block = Block(block_data['index'], block_data['data'], block_data['previous_hash'])
        new_block.timestamp = block_data['timestamp']
        new_block.hash = block_data['hash']
        new_block.nonce = block_data['nonce']
        election_chain.chain.append(new_block)
        
        # Determine prefix hashes gracefully from new_block data
        vid_prefix = "UNKNOWN"
        try: vid_prefix = base64.b64encode(hashlib.sha256(new_block.data['voter_id'].encode()).digest()).decode()[:8]
        except: pass
        
        socketio.emit('new_block', {
            'block_index': new_block.index,
            'voter_id_hash_prefix': vid_prefix,
            'nonce': new_block.nonce,
            'block_hash_preview': new_block.hash[:16],
            'timestamp': new_block.timestamp
        })
        return jsonify({"status": "synced"}), 200
    return jsonify({"status": "ignored"}), 200

# Error Handlers
@app.errorhandler(401)
def unauthorized(e):
    return render_template('error/401.html'), 401

@app.errorhandler(403)
def forbidden(e):
    return render_template('error/403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error/500.html'), 500

if __name__ == '__main__':
    socketio.run(app, debug=False, port=PORT, host='0.0.0.0')
