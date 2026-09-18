import requests
from flask import Blueprint, jsonify, request

wallet_bp = Blueprint('wallet', __name__)

# ─── Constants ─────────────────────────────────────────────────────────────

MEME_QUERIES = {
    'solana':   ['solana', 'sol meme', 'pump fun', 'bonk', 'wif', 'popcat'],
    'ethereum': ['ethereum meme', 'pepe', 'shib', 'floki', 'mog'],
    'all':      ['solana meme', 'ethereum meme', 'pump fun', 'pepe', 'bonk', 'wif'],
}

# ─── Helpers ───────────────────────────────────────────────────────────────

def get_token_price(symbol: str, chain: str) -> float:
    """
    Get price by searching DexScreener for the token symbol
    and picking the highest-liquidity pair on the correct chain.
    """
    try:
        res = requests.get(
            f'https://api.dexscreener.com/latest/dex/search?q={symbol}%2FUSDC',
            timeout=8
        )
        res.raise_for_status()
        pairs = res.json().get('pairs', []) or []

        # Filter to correct chain, sort by liquidity
        chain_pairs = [
            p for p in pairs
            if p.get('chainId') == chain
            and p.get('baseToken', {}).get('symbol', '').upper() == symbol.upper()
        ]
        chain_pairs.sort(key=lambda p: float(p.get('liquidity', {}).get('usd') or 0), reverse=True)

        if chain_pairs:
            return float(chain_pairs[0].get('priceUsd') or 0)
        return 0.0
    except Exception:
        return 0.0


def fetch_dexscreener_pairs(query: str) -> list:
    """Search DexScreener for pairs matching a query."""
    try:
        res = requests.get(
            f'https://api.dexscreener.com/latest/dex/search?q={query}',
            timeout=8
        )
        res.raise_for_status()
        return res.json().get('pairs', []) or []
    except Exception:
        return []


def fetch_trending_pairs(chain: str) -> list:
    """Fetch trending/boosted tokens from DexScreener."""
    try:
        res = requests.get(
            'https://api.dexscreener.com/token-boosts/top/v1',
            timeout=8
        )
        if not res.ok:
            return []
        items = res.json() or []

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
        eth_price = get_token_price('WETH', 'ethereum')
        sol_price = get_token_price('SOL', 'solana')

        # Fallback: try alternate symbols if 0
        if eth_price == 0:
            eth_price = get_token_price('ETH', 'ethereum')
        if sol_price == 0:
            sol_price = get_token_price('WSOL', 'solana')

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
        eth_price = get_token_price('WETH', 'ethereum')
        sol_price = get_token_price('SOL', 'solana')

        return jsonify({
            'total_usd': 0,
            'eth': {'balance': 0, 'usd': 0, 'price': eth_price},
            'sol': {'balance': 0, 'usd': 0, 'price': sol_price},
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
