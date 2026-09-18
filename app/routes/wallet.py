import requests
from flask import Blueprint, jsonify, request

wallet_bp = Blueprint('wallet', __name__)

# ─── Trending meme coins from DexScreener ──────────────────────────────────

MEME_QUERIES = {
    'solana':   ['solana', 'sol meme', 'pump fun', 'bonk', 'wif', 'popcat'],
    'ethereum': ['ethereum meme', 'pepe', 'shib', 'floki', 'mog'],
    'all':      ['solana meme', 'ethereum meme', 'pump fun', 'pepe', 'bonk', 'wif'],
}

CHAIN_MAP = {
    'solana':   'solana',
    'ethereum': 'ethereum',
}

def fetch_dexscreener_pairs(query: str) -> list:
    """Search DexScreener for pairs matching a query."""
    try:
        url = f"https://api.dexscreener.com/latest/dex/search?q={query}"
        res = requests.get(url, timeout=8)
        data = res.json()
        return data.get('pairs', []) or []
    except Exception:
        return []

def fetch_trending_pairs(chain: str) -> list:
    """Fetch trending/boosted tokens from DexScreener token profiles."""
    try:
        # DexScreener trending endpoint (no key needed)
        url = "https://api.dexscreener.com/token-boosts/top/v1"
        res = requests.get(url, timeout=8)
        items = res.json() if res.ok else []
        
        pairs = []
        for item in items[:30]:
            token_chain = item.get('chainId', '')
            # Filter by chain if needed
            if chain != 'all':
                if token_chain != chain:
                    continue
            if token_chain not in ('solana', 'ethereum'):
                continue
            
            token_addr = item.get('tokenAddress', '')
            if not token_addr:
                continue
            
            # Fetch pair data for this token
            pair_url = f"https://api.dexscreener.com/latest/dex/tokens/{token_addr}"
            pair_res = requests.get(pair_url, timeout=6)
            if not pair_res.ok:
                continue
            pair_data = pair_res.json().get('pairs', [])
            if pair_data:
                pairs.append(pair_data[0])  # Best pair for this token
        
        return pairs
    except Exception:
        return []

def normalize_pair(pair: dict) -> dict | None:
    """Convert a DexScreener pair object into our Token schema."""
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
            'name':        base.get('name', 'Unknown'),
            'symbol':      base.get('symbol', '?'),
            'address':     base.get('address', ''),
            'price_usd':   price,
            'change_24h':  float(change.get('h24') or 0),
            'volume_24h':  float(vol.get('h24') or 0),
            'liquidity':   float(liq.get('usd') or 0),
            'chain':       chain_id,
            'pair_address': pair.get('pairAddress', ''),
            'dex':         pair.get('dexId', ''),
        }
    except Exception:
        return None

@wallet_bp.route('/markets', methods=['GET'])
def get_markets():
    chain = request.args.get('chain', 'all').lower()  # 'all' | 'solana' | 'ethereum'

    all_pairs = []
    seen_addresses = set()

    # ── Strategy 1: Search popular meme coin queries ──────────────────────
    queries = MEME_QUERIES.get(chain, MEME_QUERIES['all'])
    for q in queries:
        pairs = fetch_dexscreener_pairs(q)
        for p in pairs[:10]:  # top 10 per query
            addr = p.get('baseToken', {}).get('address', '')
            if addr and addr not in seen_addresses:
                token = normalize_pair(p)
                if token:
                    # Apply chain filter
                    if chain != 'all' and token['chain'] != chain:
                        continue
                    seen_addresses.add(addr)
                    all_pairs.append(token)

    # ── Strategy 2: Trending boosted tokens ───────────────────────────────
    boosted = fetch_trending_pairs(chain)
    for p in boosted:
        addr = p.get('baseToken', {}).get('address', '')
        if addr and addr not in seen_addresses:
            token = normalize_pair(p)
            if token:
                seen_addresses.add(addr)
                all_pairs.append(token)

    # ── Sort by volume (highest first), cap at 100 ────────────────────────
    all_pairs.sort(key=lambda x: x['volume_24h'], reverse=True)
    all_pairs = all_pairs[:100]

    return jsonify({'tokens': all_pairs, 'count': len(all_pairs)})
