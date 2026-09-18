import requests
from flask import Blueprint, jsonify, request

wallet_bp = Blueprint('wallet', __name__)

# ─── Constants ─────────────────────────────────────────────────────────────

MEME_QUERIES = {
    'solana':   ['solana', 'sol meme', 'pump fun', 'bonk', 'wif', 'popcat'],
    'ethereum': ['ethereum meme', 'pepe', 'shib', 'floki', 'mog'],
    'all':      ['solana meme', 'ethereum meme', 'pump fun', 'pepe', 'bonk', 'wif'],
}

# ─── Price Helpers ─────────────────────────────────────────────────────────

def get_prices_binance() -> dict:
    """Primary: Binance public ticker — no key, always reliable."""
    try:
        eth_res = requests.get(
            'https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT',
            timeout=8
        )
        sol_res = requests.get(
            'https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT',
            timeout=8
        )
        eth_price = float(eth_res.json().get('price', 0))
        sol_price = float(sol_res.json().get('price', 0))
        print(f'[binance] ETH={eth_price} SOL={sol_price}')
        return {'eth': eth_price, 'sol': sol_price}
    except Exception as e:
        print(f'[binance] FAILED: {e}')
        return {'eth': 0, 'sol': 0}


def get_prices_coingecko() -> dict:
    """Fallback: CoinGecko simple price."""
    try:
        res = requests.get(
            'https://api.coingecko.com/api/v3/simple/price'
            '?ids=ethereum,solana&vs_currencies=usd',
            headers={'accept': 'application/json'},
            timeout=10
        )
        print(f'[coingecko] status={res.status_code}')
        data = res.json()
        return {
            'eth': float(data.get('ethereum', {}).get('usd', 0)),
            'sol': float(data.get('solana',   {}).get('usd', 0)),
        }
    except Exception as e:
        print(f'[coingecko] FAILED: {e}')
        return {'eth': 0, 'sol': 0}


def get_live_prices() -> dict:
    """Try Binance first, fall back to CoinGecko."""
    prices = get_prices_binance()
    if prices['eth'] == 0 or prices['sol'] == 0:
        fallback = get_prices_coingecko()
        if prices['eth'] == 0:
            prices['eth'] = fallback['eth']
        if prices['sol'] == 0:
            prices['sol'] = fallback['sol']
    return prices


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
