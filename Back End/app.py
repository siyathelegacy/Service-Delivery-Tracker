# backend/app.py
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from web3 import Web3
import openai
import socketio
import asyncio

# local modules
from hashing import sha256_bytes32_hex
from models import engine, reports

load_dotenv()

RPC = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDR = os.getenv("CONTRACT_ADDR", "0x8A32770bca516b98804D9CD17999535167a975Dc")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")  # change as needed

openai.api_key = OPENAI_KEY

# Load ABI
with open(os.path.join(os.path.dirname(__file__), "..", "contracts", "ServiceDeliveryTracker.json")) as f:
    ABI = json.load(f)["abi"]

# Web3
w3 = Web3(Web3.HTTPProvider(RPC))
if not w3.is_connected():
    print("WARNING: Web3 not connected. Check RPC_URL in .env")

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDR), abi=ABI)

# FastAPI + Socket.IO
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# DB connection helper
def get_conn():
    return engine.connect()

# Data models
class ReportIn(BaseModel):
    description: str
    category: str
    location: str = ""
    user: str

# AI helper
def generate_ai_response_text(report: ReportIn):
    # Simple prompt — customize for local language/municipality naming
    prompt = (
        f"You are a municipal assistant specialized in student off-campus issues in South African cities.\n\n"
        f"Report details:\n"
        f"- Category: {report.category}\n"
        f"- Description: {report.description}\n"
        f"- Location: {report.location}\n\n"
        f"Write a concise confirmation to the student (2-4 sentences) that:\n"
        f"1) their report has been recorded,\n"
        f"2) it has been routed to the relevant municipal department and/or university stakeholder (e.g. Student Affairs),\n"
        f"3) provide an expected timeframe or next step.\n"
        f"Keep it polite and actionable."
    )

    # Use OpenAI ChatCompletion (adjust for Gemini if using another API)
    try:
        resp = openai.ChatCompletion.create(
            model=AI_MODEL,
            messages=[{"role":"user","content":prompt}],
            max_tokens=150,
            temperature=0.2
        )
        text = resp["choices"][0]["message"]["content"].strip()
        return text
    except Exception as e:
        print("AI generation error:", e)
        # fallback message
        return ("Thank you — your report has been recorded and forwarded to the relevant municipal "
                "department and university housing office. They will follow up in due course.")

# POST /api/report — main route
@app.post("/api/report")
async def submit_report(r: ReportIn):
    # canonical payload for hashing
    payload = {
        "description": r.description,
        "category": r.category,
        "location": r.location,
        "user": r.user,
        "timestamp": datetime.utcnow().isoformat()
    }
    payload_hash = sha256_bytes32_hex(payload)

    # 1) generate AI response
    ai_response = generate_ai_response_text(r)

    # 2) create tx to anchor on-chain
    try:
        account = w3.eth.account.from_key(PRIVATE_KEY)
        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.anchorReport(
            int(time.time()),  # use epoch as id; you can use server-side autoinc
            Web3.to_bytes(hexstr=payload_hash),
            r.category
        ).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": 300000,
            "gasPrice": w3.to_wei("2", "gwei")
        })
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_hash_hex = tx_hash.hex()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain anchor failed: {e}")

    # 3) store metadata in DB
    conn = get_conn()
    ins = reports.insert().values(
        hash=payload_hash,
        description=r.description,
        category=r.category,
        location=r.location,
        user=r.user,
        ai_response=ai_response,
        tx_hash=tx_hash_hex,
        created_at=datetime.utcnow().isoformat()
    )
    res = conn.execute(ins)

    # 4) Emit socket notification (non-blocking)
    payload_out = {
        "id": res.inserted_primary_key[0],
        "category": r.category,
        "location": r.location,
        "user": r.user,
        "ai_response": ai_response,
        "tx_hash": tx_hash_hex
    }
    await sio.emit("new_report", payload_out)

    return JSONResponse({"success": True, "ai_response": ai_response, "tx_hash": tx_hash_hex})

# GET stats
@app.get("/api/reports/stats")
def stats():
    conn = get_conn()
    total = conn.execute(text("SELECT COUNT(*) FROM reports")).scalar()
    unique = conn.execute(text("SELECT COUNT(DISTINCT user) FROM reports")).scalar()
    return {"totalReports": int(total), "uniqueReporters": int(unique)}

# GET user reports
@app.get("/api/reports/user/{address}")
def user_reports(address: str):
    conn = get_conn()
    rows = conn.execute(text("SELECT * FROM reports WHERE user = :u ORDER BY id DESC"), {"u": address}).fetchall()
    return [dict(r) for r in rows]

# GET all reports (admin)
@app.get("/api/reports/all")
def all_reports():
    conn = get_conn()
    rows = conn.execute(text("SELECT * FROM reports ORDER BY id DESC")).fetchall()
    return [dict(r) for r in rows]

# Contract info endpoint for frontend
@app.get("/api/contract-info")
def contract_info():
    return {"address": CONTRACT_ADDR, "abi": ABI}

# socket handlers (optional)
@sio.event
async def connect(sid, environ):
    print("Socket connected:", sid)

@sio.event
async def disconnect(sid):
    print("Socket disconnected:", sid)

# To run: use uvicorn pointing to this ASGI app wrapper:
# uvicorn backend.app:socket_app --host 0.0.0.0 --port 8000
