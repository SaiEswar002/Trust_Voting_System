#!/bin/bash

# Navigate to the correct directory
cd "$(dirname "$0")"

echo "Initializing Virtual Environment..."
source venv/bin/activate

echo "Terminating any existing standalone server instances..."
pkill -f "app.py" 
sleep 1

echo "Destroying old unified cryptographic keys to ensure a clean sync..."
rm -f backend/shared_keys.json

echo "Booting up the 6-Node Proof-of-Work Voting Network!"
echo "----------------------------------------------------"

python app.py 5001 1 &
echo "[✔] Node 1 (Booth 1) Online at http://127.0.0.1:5001"
sleep 3 # Critical: Allow Node 1 to generate and write the shared_keys.json before peers boot

python app.py 5002 2 &
echo "[✔] Node 2 (Booth 2) Online at http://127.0.0.1:5002"

python app.py 5003 3 &
echo "[✔] Node 3 (Booth 3) Online at http://127.0.0.1:5003"

python app.py 5004 4 &
echo "[✔] Node 4 (Booth 4) Online at http://127.0.0.1:5004"

python app.py 5005 5 &
echo "[✔] Node 5 (Booth 5) Online at http://127.0.0.1:5005"

python app.py 5006 6 &
echo "[✔] Node 6 (Booth 6) Online at http://127.0.0.1:5006"

echo "----------------------------------------------------"
echo "All Distributed Distributed Nodes currently running in background!"
echo "Use 'pkill -f app.py' to terminate the entire network."
