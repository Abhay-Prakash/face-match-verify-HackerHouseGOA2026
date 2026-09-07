"""
Shared Web3 configuration for Polygon Amoy testnet interaction.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# Polygon Amoy testnet (chain ID 80002)
AMOY_CHAIN_ID = 80002

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"


def load_project_env() -> None:
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def require_env(name: str) -> str:
    load_project_env()
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is not set. Add it to your local .env file.")
    return value


def get_web3(rpc_url: str | None = None) -> Web3:
    load_project_env()
    rpc_url = rpc_url or require_env("RPC_URL")
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    # Polygon PoS Amoy uses PoA-style block extraData.
    # Web3.py requires this middleware to decode those block headers.
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    if not w3.is_connected():
        raise RuntimeError(f"Could not connect to RPC endpoint: {rpc_url}")
    chain_id = w3.eth.chain_id
    if chain_id != AMOY_CHAIN_ID:
        raise RuntimeError(
            f"Expected Polygon Amoy (chain ID {AMOY_CHAIN_ID}), got chain ID {chain_id}. "
            "Check your RPC_URL points at Amoy, not mainnet or another network."
        )
    return w3


def payload_hash_to_bytes32(payload_hash_hex: str) -> bytes:
    """
    Convert the 64-char SHA-256 hex digest from hasher.py into bytes32
    for contract calls. Accepts with or without 0x prefix.
    """
    normalized = payload_hash_hex.lower().removeprefix("0x")
    if len(normalized) != 64:
        raise ValueError(f"payload hash must be 32 bytes (64 hex chars), got {len(normalized)}")
    return bytes.fromhex(normalized)
