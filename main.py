from fastapi import FastAPI, HTTPException
from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()
rpc_url = os.getenv("RPC_URL")
if not rpc_url:
    raise RuntimeError("RPS_URL is not set. Copy .env.example to .env and fill it in.")
    

app = FastAPI()

w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 5},))

@app.get("/")
def root():
    return {"message": "hello"}

@app.get("/api/v1/blockchain/status")
def status():
    try:
        chain_id = w3.eth.chain_id
        block_number = w3.eth.block_number
    except Exception:
        raise HTTPException(status_code=503, detail="Ethereum node unavailable")
    return {"chain_id": chain_id, "block_number": block_number}