"""
Upload a canonical payload hash to HashRegistry on Polygon Amoy.

Usage:
    python -m src.blockchain.upload <payload_hash_hex>

Or import store_hash() from main.py / tests.
"""

import sys
from pathlib import Path

from eth_account import Account
from web3 import Web3

from src.blockchain.chain_config import AMOY_CHAIN_ID, get_web3, payload_hash_to_bytes32, require_env
from src.blockchain.contract.compile import load_artifact

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _get_contract(w3: Web3, contract_address: str):
    artifact = load_artifact()
    return w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=artifact["abi"])


def store_hash(
    payload_hash_hex: str,
    rpc_url: str | None = None,
    private_key: str | None = None,
    contract_address: str | None = None,
) -> dict:
    """
    Call storeHash(bytes32) on HashRegistry. Returns tx metadata including
    a genuine testnet transaction hash and block number.
    """
    rpc_url = rpc_url or require_env("RPC_URL")
    private_key = private_key or require_env("PRIVATE_KEY")
    contract_address = contract_address or require_env("CONTRACT_ADDRESS")

    w3 = get_web3(rpc_url)
    account = Account.from_key(private_key)
    contract = _get_contract(w3, contract_address)
    hash_bytes32 = payload_hash_to_bytes32(payload_hash_hex)

    nonce = w3.eth.get_transaction_count(account.address)
    tx = contract.functions.storeHash(hash_bytes32).build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "chainId": AMOY_CHAIN_ID,
            "gas": 200_000,
            "maxFeePerGas": w3.to_wei("50", "gwei"),
            "maxPriorityFeePerGas": w3.to_wei("30", "gwei"),
        }
    )

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"storeHash transaction sent: {tx_hash.hex()}")
    print("Waiting for confirmation...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    if receipt.status != 1:
        raise RuntimeError(f"storeHash transaction reverted: {tx_hash.hex()}")

    return {
        "contract_address": contract_address,
        "payload_hash": payload_hash_hex.lower().removeprefix("0x"),
        "tx_hash": tx_hash.hex(),
        "block_number": receipt.blockNumber,
        "from_address": account.address,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m src.blockchain.upload <payload_hash_hex>", file=sys.stderr)
        return 1

    try:
        result = store_hash(sys.argv[1])
        print("\n=== Upload successful ===")
        print(f"Payload hash:  {result['payload_hash']}")
        print(f"Block number:  {result['block_number']}")
        print(f"Tx hash:       {result['tx_hash']}")
        return 0
    except Exception as exc:
        print(f"Upload failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.path.insert(0, str(PROJECT_ROOT))
    raise SystemExit(main())
