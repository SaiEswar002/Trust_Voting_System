// app.js
document.addEventListener('DOMContentLoaded', () => {
    
    // --- State Variables ---
    let currentVoterId = document.getElementById('voter-id') ? document.getElementById('voter-id').value : null;
    let selectedVector = null;

    // --- DOM Elements ---
    const authSection = document.getElementById('auth-section');
    const votingSection = document.getElementById('voting-section');
    const processingSection = document.getElementById('processing-section');
    const receiptSection = document.getElementById('receipt-section');
    
    const fingerprintHashInput = document.getElementById('fingerprint_hash');
    const authForm = document.getElementById('auth-form');
    let authMessage = document.getElementById('auth-message');
    
    const candidateCards = document.querySelectorAll('.candidate-card');
    const confirmBox = document.getElementById('confirm-box');
    const selectedPartySpan = document.getElementById('selected-party');
    const encryptBtn = document.getElementById('encrypt-btn');
    
    const terminalLogs = document.getElementById('terminal-logs');
    const displayReceiptId = document.getElementById('display-receipt-id');
    const qrImage = document.getElementById('qr-code-img');
    const qrPlaceholder = document.getElementById('qr-placeholder');
    const verifyLink = document.getElementById('verify-receipt-link');

    // --- Step 2: Terminal Authentication Call ---
    if (authForm) {
        authForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            authMessage.className = 'message hidden';
            authMessage.innerText = '';
            
            const fp = fingerprintHashInput.value;
            
            if(!currentVoterId || !fp) {
                authMessage.innerText = "Please provide fingerprint hash.";
                authMessage.className = 'message flash-error';
                authMessage.classList.remove('hidden');
                return;
            }

            try {
                const res = await fetch('/api/authenticate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ voter_id: currentVoterId, fingerprint_hash: fp })
                });
                const data = await res.json();
                
                if(res.ok) {
                    authSection.classList.add('hidden');
                    votingSection.classList.remove('hidden');
                } else {
                    authMessage.innerText = data.message;
                    authMessage.className = 'message flash-error';
                    authMessage.classList.remove('hidden');
                }
            } catch (err) {
                authMessage.innerText = "Network error connecting to Node.";
                authMessage.className = 'message flash-error';
                authMessage.classList.remove('hidden');
            }
        });
    }

    // --- Step 3: Selection ---
    candidateCards.forEach(card => {
        card.addEventListener('click', () => {
            candidateCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            
            const index = parseInt(card.getAttribute('data-index'));
            // Create [0,0,0] vector, set selected index to 1
            selectedVector = [0, 0, 0];
            selectedVector[index] = 1;
            
            // Navigate the DOM generically
            const partyName = card.querySelector('h4').innerText;
            selectedPartySpan.innerText = partyName;
            
            confirmBox.classList.remove('hidden');
        });
    });

    // --- Step 4, 5, 6: Encryption and Blockchain Call ---
    if (encryptBtn) {
        encryptBtn.addEventListener('click', async () => {
            
            const voteFingerprintHash = document.getElementById('vote_fingerprint_hash').value;
            if(!voteFingerprintHash) {
                alert("Please re-enter your biometric fingerprint hash to sign the transaction.");
                return;
            }

            // Switch purely to Processing UI
            votingSection.classList.add('hidden');
            processingSection.classList.remove('hidden');
            
            // Simulate logs sequentially
            addLog("> Requesting Election Authority Public Key...");
            await sleep(800);
            addLog("> Constructing vote vector [" + selectedVector.join(",") + "]");
            await sleep(800);
            addLog("> Applying Paillier Homomorphic Encryption to vector elements...");
            await sleep(1500);
            addLog("> ⚠ [SECURE WIPE] Destroying raw vote vector from memory...");
            await sleep(500);
            addLog("> Bundling ciphertext & Generating Zero-Knowledge Proof...");
            
            try {
                const res = await fetch('/api/vote', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        voter_id: currentVoterId,
                        vote_vector: selectedVector,
                        fingerprint_hash: voteFingerprintHash
                    })
                });
                
                const data = await res.json();
                
                if(res.ok) {
                    addLog("> Broadcasting ZKP payload to P2P Blockchain Network...");
                    await sleep(1000);
                    addLog("> Consensus reached. Block secured.");
                    await sleep(500);
                    
                    // Show Departure step
                    processingSection.classList.add('hidden');
                    receiptSection.classList.remove('hidden');
                    
                    displayReceiptId.innerText = data.receipt_id;
                    qrImage.src = data.qr_image;
                    qrImage.style.display = 'block';
                    qrPlaceholder.style.display = 'none';
                    verifyLink.href = '/verify?receipt_id=' + data.receipt_id;
                    
                } else {
                    addLog("> ERROR: " + data.message);
                    alert("Error: " + data.message);
                    setTimeout(() => window.location.reload(), 2000);
                }
                
            } catch(err) {
                addLog("> ERROR: Failed to communicate with blockchain node.");
            }
        });
    }

    // Helpers
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function addLog(text) {
        if (!terminalLogs) return;
        const p = document.createElement('p');
        p.innerText = text;
        terminalLogs.appendChild(p);
        terminalLogs.scrollTop = terminalLogs.scrollHeight;
    }
});
