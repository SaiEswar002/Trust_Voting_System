// websocket.js
// Client side WebSocket integration for Admin and Explorer panels

document.addEventListener('DOMContentLoaded', () => {
    // Only initialize socket connection if SocketIO is loaded in the page
    if (typeof io !== 'undefined') {
        const socket = io();
        
        const wsIndicator = document.getElementById('ws-indicator');
        const wsStatusText = document.getElementById('ws-status-text');

        socket.on('connect', () => {
            console.log('WebSocket connected');
            if(wsIndicator) {
                wsIndicator.style.display = 'inline-block';
                wsStatusText.innerText = 'WebSocket LIVE';
                wsStatusText.style.color = 'var(--success)';
            }
        });

        socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            if(wsIndicator) {
                wsIndicator.style.display = 'none';
                wsStatusText.innerText = 'WebSocket Offline';
                wsStatusText.style.color = 'var(--text-muted)';
            }
        });

        // Event: new_block (Explorer page primarily)
        socket.on('new_block', (payload) => {
            const container = document.getElementById('blocks-container');
            if (container) {
                // Prepend new row to the blocks container
                const div = document.createElement('div');
                div.className = 'card flash-row'; // contains the animation
                div.style.marginBottom = '0';
                div.style.padding = '1.5rem';
                div.id = `block-${payload.block_index}`;

                div.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-weight: 600; color: var(--primary-teal);">Block #${payload.block_index} <span style="font-size: 0.75rem; color: var(--success); margin-left: 8px;">[NEW]</span></span>
                    </div>
                    <p style="font-family: monospace; font-size: 0.8rem; color: var(--text-muted); word-break: break-all;"><strong>Hash Prefix:</strong> ${payload.block_hash_preview}...</p>
                    <p style="font-family: monospace; font-size: 0.8rem; color: var(--text-muted); word-break: break-all;"><strong>Voter Prefix:</strong> ${payload.voter_id_hash_prefix}</p>
                    <p style="font-family: monospace; font-size: 0.8rem; color: var(--text-muted); word-break: break-all;"><strong>Nonce:</strong> ${payload.nonce}</p>
                `;
                container.prepend(div);
                
                // Remove the empty state or old blocks if we want to limit DOM size
            }
        });

        // Event: voter_status_change (Admin page primarily)
        socket.on('voter_status_change', (payload) => {
            const statusSpan = document.getElementById(`voter-status-${payload.voter_id}`);
            if (statusSpan) {
                statusSpan.className = 'status-badge status-cast';
                statusSpan.innerText = 'Vote Cast';
                
                const row = document.getElementById(`voter-row-${payload.voter_id}`);
                if (row) {
                    row.classList.add('flash-row');
                    setTimeout(() => row.classList.remove('flash-row'), 1500);
                }
            }
        });

        // Event: election_state_change (Any page extending base) 
        socket.on('election_state_change', (payload) => {
            // Update navbar badge
            const headerBadge = document.getElementById('header-election-status');
            const footerBadge = document.getElementById('footer-election-status');
            
            if (headerBadge) {
                headerBadge.className = `status-badge status-${payload.new_state.toLowerCase()}`;
                headerBadge.innerText = payload.new_state;
            }
            if (footerBadge) {
                footerBadge.className = `status-badge status-${payload.new_state.toLowerCase()}`;
                footerBadge.innerText = payload.new_state;
            }
            
            const controlBadge = document.getElementById('control-election-state');
            if (controlBadge) {
                 controlBadge.className = `status-badge status-${payload.new_state.toLowerCase()}`;
                 controlBadge.innerText = payload.new_state;
                 
                 // Reload the page after 2 seconds to update transition buttons if on admin
                 setTimeout(() => window.location.reload(), 2000);
            }

            // Show Toast (Using minimal JS creation)
            const toast = document.createElement('div');
            toast.style.position = 'fixed';
            toast.style.bottom = '20px';
            toast.style.right = '20px';
            toast.style.backgroundColor = 'var(--primary-teal)';
            toast.style.color = 'white';
            toast.style.padding = '12px 24px';
            toast.style.borderRadius = '6px';
            toast.style.boxShadow = 'var(--elevation-2)';
            toast.style.zIndex = '9999';
            toast.style.display = 'flex';
            toast.style.flexDirection = 'column';
            toast.style.gap = '4px';
            
            toast.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 4px; margin-bottom: 4px;">
                    <strong>Election State Update</strong>
                    <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: white; cursor: pointer;">&times;</button>
                </div>
                <div style="font-size: 0.9rem;">
                    State transitioned to <strong>${payload.new_state}</strong> by ${payload.changed_by}.
                </div>
            `;
            
            document.body.appendChild(toast);
            
            // Auto-dismiss after 8 seconds
            setTimeout(() => {
                if (toast.parentElement) toast.remove();
            }, 8000);
        });
    }
});
