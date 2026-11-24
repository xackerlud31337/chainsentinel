from fastapi import FastAPI, HTTPException
from web3 import Web3

app = FastAPI()

w3 = Web3(Web3.HTTPProvider("https://ethereum-rpc.publicnode.com", request_kwargs={"timeout": 5},))

@app.get("/")
def root():
    return {"message": "hello"}

@app.get("/api/v1/blockchain/status")
def status():
    try:
        chain_id = w3.eth.chain_id
        block_number = w3.eth.block_number
    except Exception:
        HTTPException(status_code=503, detail="Ethereum node unavailable")
    return {"chain_id": chain_id, "block_number": block_number}