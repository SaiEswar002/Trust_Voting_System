document.addEventListener('DOMContentLoaded', () => {

    // ── SHA-256 via Web Crypto API ──────────────────────────────────────────
    // Raw biometric strings are hashed client-side and never transmitted in plaintext.
    async function sha256(message) {
        const msgBuffer = new TextEncoder().encode(message);
        const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
        return Array.from(new Uint8Array(hashBuffer))
            .map(b => b.toString(16).padStart(2, '0')).join('');
    }

    let currentVoterId = null;
    let selectedVector = null;

    // --- DOM Elements ---
    const authSection = document.getElementById('auth-section');
    const votingSection = document.getElementById('voting-section');
    const processingSection = document.getElementById('processing-section');
    const receiptSection = document.getElementById('receipt-section');
    
    const scannerBox = document.getElementById('scanner-box');
    const fingerprintHashInput = document.getElementById('fingerprint_hash');
    const authForm = document.getElementById('auth-form');
    const authMessage = document.getElementById('auth-message');
    
    const candidateCards = document.querySelectorAll('.candidate-card');
    const confirmBox = document.getElementById('confirm-box');
    const selectedPartySpan = document.getElementById('selected-party');
    const encryptBtn = document.getElementById('encrypt-btn');
    
    const terminalLogs = document.getElementById('terminal-logs');
    const powerCutBtn = document.getElementById('power-cut-btn');
    const displayReceiptId = document.getElementById('display-receipt-id');
    const resetBtn = document.getElementById('reset-btn');
    
    const viewChainBtn = document.getElementById('view-chain-btn');
    const tallyBtn = document.getElementById('tally-btn');
    const dataModal = document.getElementById('data-modal');
    const closeModal = document.getElementById('close-modal');
    const modalBody = document.getElementById('modal-body');
    const modalTitle = document.getElementById('modal-title');

    // --- Step 2: Authentication Call ---
    authForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        authMessage.className = 'message hidden';
        authMessage.innerText = '';
        
        const vid = document.getElementById('voter-id').value;
        const fp = fingerprintHashInput.value;

        if(!vid || !fp) {
            authMessage.innerText = "Please provide Voter ID and fingerprint hash.";
            authMessage.className = 'message error';
            return;
        }

        // Hash raw biometric BEFORE sending — raw value never leaves browser
        const hashedFp = await sha256(fp);
        fingerprintHashInput.value = ''; // wipe raw value from DOM immediately

        try {
            const res = await fetch('/authenticate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ voter_id: vid, fingerprint_hash: hashedFp })
            });
            const data = await res.json();
            
            if(res.ok) {
                currentVoterId = vid; // Store authorized voter in session memory
                authSection.classList.add('hidden');
                votingSection.classList.remove('hidden');
            } else {
                authMessage.innerText = data.message;
                authMessage.className = 'message error';
            }
        } catch (err) {
            authMessage.innerText = "Network error connecting to DB.";
            authMessage.className = 'message error';
        }
    });

    // --- Step 3: Selection ---
    candidateCards.forEach(card => {
        card.addEventListener('click', () => {
            candidateCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            
            const index = parseInt(card.getAttribute('data-index'));
            // Create [0,0,0] vector, set selected index to 1
            selectedVector = [0, 0, 0];
            selectedVector[index] = 1;
            
            const partyName = card.querySelector('h4').innerText;
            selectedPartySpan.innerText = partyName;
            
            confirmBox.classList.remove('hidden');
        });
    });

    // --- Step 4, 5, 6: Encryption and Blockchain Call ---
    encryptBtn.addEventListener('click', async () => {
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
            const rawVoteFp = document.getElementById('vote_fingerprint_hash').value;
            if(!rawVoteFp) {
                addLog("> ERROR: Please enter your fingerprint hash.");
                return;
            }

            // Hash raw biometric BEFORE sending — raw value never leaves browser
            addLog("> Hashing biometric signature (SHA-256, client-side)...");
            const hashedVoteFp = await sha256(rawVoteFp);
            document.getElementById('vote_fingerprint_hash').value = ''; // wipe raw

            const res = await fetch('/vote', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    voter_id: currentVoterId,
                    vote_vector: selectedVector,
                    fingerprint_hash: hashedVoteFp
                })
            });
            
            const data = await res.json();
            
            if(res.ok) {
                addLog("> Broadcasting ZKP payload to Blockchain networks...");
                await sleep(1000);
                addLog("> Consensus reached. Block mined.");
                await sleep(500);
                
                // Show Departure step
                processingSection.classList.add('hidden');
                receiptSection.classList.remove('hidden');
                
                displayReceiptId.innerText = data.receipt_id;
            } else {
                addLog("> ERROR: " + data.message);
            }
            
        } catch(err) {
            addLog("> ERROR: Failed to communicate with blockchain node.");
        }
    });

    // --- Step 7: Reset Booth ---
    resetBtn.addEventListener('click', () => {
        // Clear all states
        currentVoterId = null;
        selectedVector = null;
        document.getElementById('voter-id').value = '';
        fingerprintHashInput.value = '';
        document.getElementById('vote_fingerprint_hash').value = '';
        
        candidateCards.forEach(c => c.classList.remove('selected'));
        confirmBox.classList.add('hidden');
        terminalLogs.innerHTML = "<p>> Initializing Homomorphic Encryption...</p>";
        
        receiptSection.classList.add('hidden');
        authSection.classList.remove('hidden');
    });

    // --- Power Cut Simulation ---
    powerCutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if(processingSection.classList.contains('hidden')) {
            alert("Power Cut simulation only works while a block is actively being encrypted/mined (Step 4,5,6).");
            return;
        }
        alert("🚨 POWER CUT SIMULATION 🚨\n\nPower to the voting machine was instantly terminated during encryption processing.\n\nBecause the block was never successfully mined or added to the chain, your partial/un-encrypted vote does not exist anymore. The blockchain is entirely atomic.\n\nRestarting system...");
        window.location.reload();
    });

    // --- Admin / Diagnostics ---
    viewChainBtn.addEventListener('click', async () => {
        const res = await fetch('/api/blockchain');
        const data = await res.json();
        modalTitle.innerText = "Blockchain State";
        modalBody.innerText = JSON.stringify(data, null, 2);
        dataModal.classList.remove('hidden');
    });

    tallyBtn.addEventListener('click', async () => {
        const res = await fetch('/api/tally');
        const data = await res.json();
        modalTitle.innerText = "Homomorphic Tally Results";
        modalBody.innerText = JSON.stringify(data, null, 2);
        dataModal.classList.remove('hidden');
    });

    closeModal.addEventListener('click', () => {
        dataModal.classList.add('hidden');
    });

    // Helpers
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function addLog(text) {
        const p = document.createElement('p');
        p.innerText = text;
        terminalLogs.appendChild(p);
        terminalLogs.scrollTop = terminalLogs.scrollHeight;
    }
});
