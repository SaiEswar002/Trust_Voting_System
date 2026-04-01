document.addEventListener('DOMContentLoaded', () => {
    const config = window.BOOTH_CONFIG;
    if(!config) return;

    document.querySelectorAll('.logo-text span').forEach(el => { 
        el.innerHTML = `True P2P Network Node <span style="background:#10b981; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; margin-left: 0.5rem; font-size: 0.8rem;">Booth ${config.booth_id} (Port ${config.port})</span>`; 
    });
    
    const scanText = document.querySelector('.scan-text');
    if(scanText) { scanText.innerText = `Click to scan fingerprint (Voter IDs B${config.booth_id}_V1 to B${config.booth_id}_V10 / Use 'b${config.booth_id}fp1' to 'b${config.booth_id}fp10')`; }

    document.querySelectorAll('.top-nav').forEach(nav => {
        if (nav.querySelector('select')) return; // Avoid duplicates
        const select = document.createElement('select');
        select.style = "padding: 0.4rem 0.8rem; border-radius: 6px; border: 2px solid var(--primary-teal); background: #f8fafc; font-weight: 600; color: var(--primary-teal); margin-right: 1rem; cursor: pointer; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);";
        
        select.onchange = function() { window.location.href = 'http://127.0.0.1:' + this.value + window.location.pathname; };
        
        for(let i=1; i<=6; i++) {
            let opt = document.createElement('option');
            opt.value = 5000 + i;
            opt.innerText = `📍 Jump to Booth ${i}`;
            if(config.port == (5000+i)) opt.selected = true;
            select.appendChild(opt);
        }
        nav.prepend(select);
    });
});
