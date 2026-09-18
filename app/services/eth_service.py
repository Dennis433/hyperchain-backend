from web3 import Web3
import requests
import os
from dotenv import load_dotenv

load_dotenv()

INFURA_KEY = os.getenv("INFURA_KEY")
ETHERSCAN_API = os.getenv("ETHERSCAN_API_KEY")

w3 = Web3(Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{INFURA_KEY}"))

def is_connected():
    try:
        return w3.is_connected()
    except Exception as e:
        return False

def get_eth_balance(address):
    try:
        checksum_address = Web3.to_checksum_address(address)
        balance_wei = w3.eth.get_balance(checksum_address)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        return str(round(balance_eth, 6))
    except Exception as e:
        return f"Error: {str(e)}"

def get_eth_transactions(address):
    try:
        url = f"https://api.etherscan.io/v2/api?chainid=1&module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API}"
        response = requests.get(url)
        data = response.json()
        results = data.get("result", [])
        print(f"Status: {data['status']}")
        print(f"Message: {data['message']}")
        print(f"Type: {type(results)}")
        if not isinstance(results, list):
            return {"error": f"Etherscan message: {results}"}
        if len(results) > 0:
            txs = results[:10]
            return [{
                "hash": tx["hash"],
                "from": tx["from"],
                "to": tx["to"],
                "value": str(round(int(tx["value"]) / 1e18, 6)) + " ETH",
                "timestamp": tx["timeStamp"],
                "gas_used": tx["gasUsed"],
                "confirmations": tx["confirmations"],
                "status": "Success" if tx["txreceipt_status"] == "1" else "Failed"
            } for tx in txs]
        return []
    except Exception as e:
        return f"Error: {str(e)}"

def get_eth_token_balances(address):
    try:
        url = f"https://api.etherscan.io/v2/api?chainid=1&module=account&action=tokentx&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API}"
        response = requests.get(url)
        data = response.json()
        results = data.get("result", [])
        if not isinstance(results, list):
            return []
        if len(results) > 0:
            tokens = {}
            for tx in results:
                symbol = tx["tokenSymbol"]
                if symbol not in tokens:
                    tokens[symbol] = {
                        "symbol": symbol,
                        "name": tx["tokenName"],
                        "contract": tx["contractAddress"],
                        "decimals": tx["tokenDecimal"]
                    }
            return list(tokens.values())
        return []
    except Exception as e:
        return f"Error: {str(e)}"

def get_gas_price():
    try:
        gas_wei = w3.eth.gas_price
        gas_gwei = w3.from_wei(gas_wei, 'gwei')
        return str(round(gas_gwei, 2)) + " Gwei"
    except Exception as e:
        return f"Error: {str(e)}"
