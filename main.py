from fastapi import FastAPI
from web3 import Web3

app = FastAPI()

w3 = Web3(Web3.HTTPProvider("https://ethereum-rpc.publicnode.com"))

@app.get("/")
def root():
    return {"message": "hello"}

@app.get("/api/v1/blockchain/status")
def status():
    return {"chain_id": w3.eth.chain_id, "block_number": w3.eth.block_number}