Service Delivery Tracker – Full Project Overview

This project is a blockchain‑powered Service Delivery Tracking system designed to monitor,
verify, and record service‑related actions using smart contracts,
a Python backend, and a simple REST API. The system ensures transparency, 
auditability, and trust by storing critical events on the Ethereum Sepolia test network.

Project Structure
service-delivery-students/
│
├── contract/
│   ├── ServiceDeliveryTracker.sol      # Solidity smart contract
│   └── abi/
│        └── ServiceDeliveryTracker.json
│
├── backend/
│   ├── app.py                          # Flask API (Web3, DB, AI logic)
│   ├── listener.py                     # Real‑time blockchain event listener
│   ├── database.db                     # Auto-created SQLite database
│   ├── requirements.txt                # Backend dependencies
│   └── .env                            # Environment variables
│
└── README.md

Features
Blockchain

Tracks service creation, verification, and completion.

Uses Ethereum Sepolia network.

Smart contract supports:

Service registration

Agent verification

Updates to service status

Event emission for backend listeners

Backend

Python Flask REST API.

Stores service metadata in a local SQLite database.

Uses Web3.py to interact with the deployed smart contract.

Listens for blockchain events and updates the database in real time.

Security

Sensitive information stored in .env file.

Admin wallet is passed during contract deployment.

API protected by a secret key.

Environment Variables

Create a .env file inside /backend with the following:

# -------------------------
# Flask / Server
# -------------------------
FLASK_SECRET=replace_with_real_secret
ENV=development

# -------------------------
# Database
# -------------------------
DB_PATH=database.db

# -------------------------
# Ethereum / Blockchain
# -------------------------
PRIVATE_KEY=replace_with_your_wallet_private_key
PUBLIC_ADDRESS=replace_with_your_public_wallet_address
INFURA_SEPOLIA_URL=https://sepolia.infura.io/v3/your_infura_project_id

CONTRACT_ADDRESS=replace_after_deploying
ABI_PATH=abi/ServiceDeliveryTracker.json

How to Get the Infura RPC URL

Create an account at https://infura.io/

Create a new project.

Select Ethereum.

Select Sepolia as the network.

Copy the RPC URL:

https://sepolia.infura.io/v3/YOUR_PROJECT_ID


Paste this into the .env file as:

INFURA_SEPOLIA_URL=https://sepolia.infura.io/v3/<your_project_id>

How to Replace FLASK_SECRET

Generate a secure secret key using:

import secrets
print(secrets.token_hex(32))


Copy the output and replace:

FLASK_SECRET=your_generated_secret

Installation & Setup
1. Install Dependencies

Inside the backend folder:

pip install -r requirements.txt

2. Run the Flask API
python app.py

3. Start the Blockchain Listener
python listener.py

Smart Contract Deployment

You can deploy the Solidity contract using:

Remix

Hardhat

Foundry

Web3.py deployment script

After deployment:

Copy the contract address into .env → CONTRACT_ADDRESS

Copy the ABI JSON file into contract/abi/

Endpoints (Flask API)
1. Register a Service
POST /register-service


Creates a new service entry and pushes the request to the blockchain.

2. Verify a Service
POST /verify

3. Complete a Service
POST /complete

4. Fetch All Services
GET /services

Event Listener

listener.py monitors blockchain events such as:

ServiceCreated

ServiceVerified

ServiceCompleted

When events are detected, the local database updates automatically.

Technologies Used

Solidity (Smart Contract)

Python / Flask (Backend)

Web3.py (Blockchain interaction)

SQLite (Local persistence)

Infura – Sepolia (Ethereum RPC)

Chainstack (optional alternative RPC provider)

Future Enhancements

Full admin dashboard

Authentication with JWT

Frontend integration

File uploads stored on IPFS

Agent grading system
