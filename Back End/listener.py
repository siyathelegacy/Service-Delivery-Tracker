# backend/listener.py
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from web3 import Web3
from sqlalchemy import text
from models import engine
from pathlib import Path

load_dotenv()
RPC = os.getenv("RPC_URL")
CONTRACT_ADDR = os.getenv("CONTRACT_ADDR", "0x8A32770bca516b98804D9CD17999535167a975Dc")

with open(os.path.join(os.path.dirname(__file__), "..", "contracts", "ServiceDeliveryTracker.json")) as f:
    ABI = json.load(f)["abi"]

w3 = Web3(Web3.HTTPProvider(RPC))
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDR), abi=ABI)

def handle_event(e):
    args = e['args']
    out = {
        "id": args['id'],
        "hash": args['hash'].hex(),
        "timestamp": args['timestamp'],
        "eventType": args['eventType'],
        "reporter": args['reporter'],
        "tx": e['transactionHash'].hex()
    }
    Path("events_out").mkdir(exist_ok=True)
    fname = Path("events_out") / f"{out['id']}_{out['tx']}.json"
    with open(fname, "w") as fh:
        json.dump(out, fh)
    print("Saved event:", fname)

def poll_loop(poll_interval=5):
    print("Listener started — polling for Anchored events")
    last_block = w3.eth.block_number
    while True:
        current = w3.eth.block_number
        if current >= last_block:
            try:
                # read recent events
                events = contract.events.Anchored.createFilter(fromBlock=max(0, last_block - 10), toBlock='latest').get_all_entries()
                for e in events:
                    handle_event(e)
                last_block = current + 1
            except Exception as ex:
                print("Listener error:", ex)
        time.sleep(poll_interval)

if __name__ == "__main__":
    poll_loop()
