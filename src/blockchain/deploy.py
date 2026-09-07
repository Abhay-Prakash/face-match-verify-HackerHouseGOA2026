"""
Deploy HashRegistry to Polygon Amoy testnet.

Usage:
    python -m src.blockchain.deploy

Requires RPC_URL and PRIVATE_KEY in .env. Saves deploy info to
data/output/deploy_info.json and prints the contract address to add
to CONTRACT_ADDRESS in .env.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from eth_account import Account
from web3 import Web3

from src.blockchain.chain_config import AMOY_CHAIN_ID, OUTPUT_DIR, get_web3, require_env
from src.blockchain.contract.compile import compile_contract

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def deploy_contract() -> dict:
    rpc_url = require_env("RPC_URL")
    private_key = require_env("PRIVATE_KEY")
    w3 = get_web3(rpc_url)

    artifact = compile_contract()
    account = Account.from_key(private_key)

    Contract = w3.eth.contract(abi=artifact["abi"], bytecode=artifact["bytecode"])
    nonce = w3.eth.get_transaction_count(account.address)

    deploy_tx_base = {
        "from": account.address,
        "nonce": nonce,
        "chainId": AMOY_CHAIN_ID,
    }
    estimated_gas = Contract.constructor().estimate_gas(deploy_tx_base)
    gas_limit = int(estimated_gas * 1.2)
    max_fee_per_gas = w3.to_wei("50", "gwei")

    tx = Contract.constructor().build_transaction(
        {
            **deploy_tx_base,
            "gas": gas_limit,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": w3.to_wei("30", "gwei"),
        }
    )

    tx_value = tx.get("value", 0)
    max_cost_wei = gas_limit * max_fee_per_gas + tx_value

    print("=== Deploy transaction fees ===")
    print(f"Estimated gas:        {estimated_gas}")
    print(f"Gas limit (+20%):     {gas_limit}")
    print(f"Max fee per gas:      {Web3.from_wei(max_fee_per_gas, 'gwei')} gwei")
    print(f"Maximum possible cost: {Web3.from_wei(max_cost_wei, 'ether')} POL")

    balance = w3.eth.get_balance(account.address)
    if balance < max_cost_wei:
        raise RuntimeError(
            "Insufficient POL for deploy: "
            f"need up to {Web3.from_wei(max_cost_wei, 'ether')} POL "
            f"(gas {gas_limit} * maxFeePerGas 50 gwei), "
            f"have {Web3.from_wei(balance, 'ether')} POL"
        )

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"Deploy transaction sent: {tx_hash.hex()}")
    print("Waiting for confirmation...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    if receipt.status != 1:
        raise RuntimeError(f"Deploy transaction reverted: {tx_hash.hex()}")

    contract_address = receipt.contractAddress
    if not contract_address:
        raise RuntimeError("Deploy receipt did not include a contract address")

    deploy_info = {
        "network": "polygon-amoy",
        "chain_id": AMOY_CHAIN_ID,
        "contract_address": contract_address,
        "deployer": account.address,
        "tx_hash": tx_hash.hex(),
        "block_number": receipt.blockNumber,
        "deployed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "solc_version": artifact["solc_version"],
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "deploy_info.json"
    out_path.write_text(json.dumps(deploy_info, indent=2), encoding="utf-8")

    print("\n=== Deploy successful ===")
    print(f"Contract address: {contract_address}")
    print(f"Block number:     {receipt.blockNumber}")
    print(f"Tx hash:          {tx_hash.hex()}")
    print(f"Saved to:         {out_path}")
    print("\nAdd this to your .env:")
    print(f"CONTRACT_ADDRESS={contract_address}")

    return deploy_info


def main() -> int:
    try:
        deploy_contract()
        return 0
    except Exception as exc:
        print(f"Deploy failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.path.insert(0, str(PROJECT_ROOT))
    raise SystemExit(main())
