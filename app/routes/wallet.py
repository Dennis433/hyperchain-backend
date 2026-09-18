import requests
from flask import Blueprint, jsonify, request

wallet_bp = Blueprint('wallet', __name__)

# ─── Constants ─────────────────────────────────────────────────────────────

MEME_QUERIES = {
    'solana':   ['solana', 'sol meme', 'pump fun', 'bonk', 'wif', 'popcat'],
    'ethereum': ['ethereum meme', 'pepe', 'shib', 'floki', 'mog'],
    'all':      ['solana meme', 'ethereum meme', 'pump fun', 'pepe', 'bonk', 'wif'],
}

# DexScreener token addresses
TOKEN_ADDRESSES = {
    'ETH': ('ethereum', '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'),  # WETH
    'SOL': ('solana',   'So11111111111111111111111111111111111111112'),   # WSOL
}

# ─── Price Helpers ─────────────────────────────────────────────────────────

def get_price_by_address(chain: str, address: str) -> float:
    """
    Fetch token price from DexScreener using contract address.
    Picks the pair with highest liquidity.
    """
    try:
        res = requests.get(
            f'https://api.dexscreener.com/latest/dex/tokens/{address}',
            timeout=8
        )
        res.raise_for_status()
        pairs = res.json().get('pairs', []) or []

        # Filter to correct chain
        chain_pairs = [p for p in pairs if p.get('chainId') == chain]

        if not chain_pairs:
            print(f'[dexscreener] no pairs found for {address} on {chain}')
            return 0.0

        # Sort by liquidity descending, pick best pair
        chain_pairs.sort(
            key=lambda p: float(p.get('liquidity', {}).get('usd') or 0),
            reverse=True
        )

        best = chain_pairs[0]
        base_addr  = best.get('baseToken',  {}).get('address', '').lower()
        price_usd  = float(best.get('priceUsd') or 0)
        price_native = float(best.get('priceNative') or 0)

        # If our token is the BASE token → priceUsd is correct
        if base_addr == address.lower():
            print(f'[dexscreener] {address} base price = {price_usd}')
            return price_usd

        # If our token is the QUOTE token → invert
        if price_native > 0:
            inverted = price_usd / price_native
            print(f'[dexscreener] {address} quote price (inverted) = {inverted}')
            return inverted

        return 0.0

    except Exception as e:
        print(f'[dexscreener] FAILED for {address}: {e}')
        return 0.0


def get_live_prices() -> dict:
    """Fetch ETH and SOL prices via DexScreener token addresses."""
    eth_chain, eth_addr = TOKEN_ADDRESSES['ETH']
    sol_chain, sol_addr = TOKEN_ADDRESSES['SOL']

    eth_price = get_price_by_address(eth_chain, eth_addr)
    sol_price = get_price_by_address(sol_chain, sol_addr)

    print(f'[prices] ETH={eth_price} SOL={sol_price}')
    return {'eth': eth_price, 'sol': sol_price}


# ─── Markets Helpers ───────────────────────────────────────────────────────

def fetch_dexscreener_pairs(query: str) -> list:
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
        prices = get_live_prices()
        return jsonify({
            'ETH': {'usd': prices['eth']},
            'SOL': {'usd': prices['sol']},
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@wallet_bp.route('/markets', methods=['GET'])
def get_markets():
    chain = request.args.get('chain', 'all').lower()

    all_pairs      = []
    seen_addresses = set()

    # Strategy 1: meme coin keyword search
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
        prices = get_live_prices()
        return jsonify({
            'total_usd': 0,
            'eth': {'balance': 0, 'usd': 0, 'price': prices['eth']},
            'sol': {'balance': 0, 'usd': 0, 'price': prices['sol']},
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
