import requests
from flask import Blueprint, jsonify, request

wallet_bp = Blueprint('wallet', __name__)

# ─── Constants ─────────────────────────────────────────────────────────────

MEME_QUERIES = {
    'solana':   ['solana', 'sol meme', 'pump fun', 'bonk', 'wif', 'popcat'],
    'ethereum': ['ethereum meme', 'pepe', 'shib', 'floki', 'mog'],
    'all':      ['solana meme', 'ethereum meme', 'pump fun', 'pepe', 'bonk', 'wif'],
}

ETH_PAIR  = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'  # USDC/ETH Uniswap v3
SOL_PAIR  = '83v8iPyZihDEjDdY8RdZddyZNyUtXngz69Lgo9Kt5d6Q'  # SOL/USDC Raydium

# ─── Helpers ───────────────────────────────────────────────────────────────

def get_eth_price() -> float:
    res = requests.get(
        f'https://api.dexscreener.com/latest/dex/pairs/ethereum/{ETH_PAIR}',
        timeout=8
    )
    return float(res.json()['pair']['priceUsd'])


def get_sol_price() -> float:
    res = requests.get(
        f'https://api.dexscreener.com/latest/dex/pairs/solana/{SOL_PAIR}',
        timeout=8
    )
    return float(res.json()['pair']['priceUsd'])


def fetch_dexscreener_pairs(query: str) -> list:
    """Search DexScreener for pairs matching a query."""
    try:
        url = f'https://api.dexscreener.com/latest/dex/search?q={query}'
        res = requests.get(url, timeout=8)
        data = res.json()
        return data.get('pairs', []) or []
    except Exception:
        return []


def fetch_trending_pairs(chain: str) -> list:
    """Fetch trending/boosted tokens from DexScreener."""
    try:
        url = 'https://api.dexscreener.com/token-boosts/top/v1'
        res = requests.get(url, timeout=8)
        items = res.json() if res.ok else []

        pairs = []
        for item in items[:30]:
            token_chain = item.get('chainId', '')
            if chain != 'all' and token_chain != chain:
                continue
            if token_chain not in ('solana', 'ethereum'):
                continue

            token_addr = item.get('tokenAddress', '')
            if not token_addr:
                continue

            pair_res = requests.get(
                f'https://api.dexscreener.com/latest/dex/tokens/{token_addr}',
                timeout=6
            )
            if not pair_res.ok:
                continue
            pair_data = pair_res.json().get('pairs', [])
            if pair_data:
                pairs.append(pair_data[0])

        return pairs
    except Exception:
        return []


def normalize_pair(pair: dict):
    """Convert a DexScreener pair into our Token schema."""
    try:
        chain_id = pair.get('chainId', '')
        if chain_id not in ('solana', 'ethereum'):
            return None

        price = float(pair.get('priceUsd') or 0)
        if price == 0:
            return None

        change = pair.get('priceChange', {})
        vol    = pair.get('volume', {})
        liq    = pair.get('liquidity', {})
        base   = pair.get('baseToken', {})

        return {
            'name':         base.get('name', 'Unknown'),
            'symbol':       base.get('symbol', '?'),
            'address':      base.get('address', ''),
            'price_usd':    price,
            'change_24h':   float(change.get('h24') or 0),
            'volume_24h':   float(vol.get('h24') or 0),
            'liquidity':    float(liq.get('usd') or 0),
            'chain':        chain_id,
            'pair_address': pair.get('pairAddress', ''),
            'dex':          pair.get('dexId', ''),
        }
    except Exception:
        return None


# ─── Routes ────────────────────────────────────────────────────────────────

@wallet_bp.route('/prices', methods=['GET'])
def get_prices():
    try:
        eth_price = get_eth_price()
        sol_price = get_sol_price()

        return jsonify({
            'ETH': {'usd': eth_price},
            'SOL': {'usd': sol_price},
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@wallet_bp.route('/markets', methods=['GET'])
def get_markets():
    chain = request.args.get('chain', 'all').lower()

    all_pairs      = []
    seen_addresses = set()

    # Strategy 1: keyword search for meme coins
    queries = MEME_QUERIES.get(chain, MEME_QUERIES['all'])
    for q in queries:
        pairs = fetch_dexscreener_pairs(q)
        for p in pairs[:10]:
            addr = p.get('baseToken', {}).get('address', '')
            if addr and addr not in seen_addresses:
                token = normalize_pair(p)
                if token:
                    if chain != 'all' and token['chain'] != chain:
                        continue
                    seen_addresses.add(addr)
                    all_pairs.append(token)

    # Strategy 2: trending/boosted tokens
    for p in fetch_trending_pairs(chain):
        addr = p.get('baseToken', {}).get('address', '')
        if addr and addr not in seen_addresses:
            token = normalize_pair(p)
            if token:
                seen_addresses.add(addr)
                all_pairs.append(token)

    all_pairs.sort(key=lambda x: x['volume_24h'], reverse=True)
    all_pairs = all_pairs[:100]

    return jsonify({'tokens': all_pairs, 'count': len(all_pairs)})


@wallet_bp.route('/portfolio/<eth_address>/<sol_address>', methods=['GET'])
def get_portfolio(eth_address, sol_address):
    try:
        eth_price = get_eth_price()
        sol_price = get_sol_price()

        return jsonify({
            'total_usd': 0,
            'eth': {'balance': 0, 'usd': 0, 'price': eth_price},
            'sol': {'balance': 0, 'usd': 0, 'price': sol_price},
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
