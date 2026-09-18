import requests

SOLANA_RPC = "https://api.mainnet-beta.solana.com"

def get_sol_balance(address):
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [address]
        }
        response = requests.post(SOLANA_RPC, json=payload)
        data = response.json()
        lamports = data["result"]["value"]
        sol = lamports / 1e9  # Convert lamports to SOL
        return str(round(sol, 6))
    except Exception as e:
        return f"Error: {str(e)}"

def get_sol_transactions(address):
    try:
        # Get recent transaction signatures
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [address, {"limit": 10}]
        }
        response = requests.post(SOLANA_RPC, json=payload)
        data = response.json()
        txs = data.get("result", [])
        return [{
            "signature": tx["signature"],
            "slot": tx["slot"],
            "timestamp": tx.get("blockTime", "N/A"),
            "status": "Success" if tx["err"] is None else "Failed"
        } for tx in txs]
    except Exception as e:
        return f"Error: {str(e)}"