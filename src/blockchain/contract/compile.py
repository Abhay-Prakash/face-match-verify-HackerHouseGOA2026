"""
Compile HashRegistry.sol via py-solc-x. Called by deploy.py and tests.
"""

from pathlib import Path

CONTRACT_DIR = Path(__file__).resolve().parent
SOL_FILE = CONTRACT_DIR / "HashRegistry.sol"
ARTIFACTS_DIR = CONTRACT_DIR / "artifacts"


def compile_contract(solc_version: str = "0.8.20") -> dict:
    """
    Compile HashRegistry.sol and return {"abi": [...], "bytecode": "0x..."}.
    Installs the requested solc binary via py-solc-x if not already present.
    """
    from solcx import compile_standard, install_solc, set_solc_version

    install_solc(solc_version)
    set_solc_version(solc_version)

    source = SOL_FILE.read_text(encoding="utf-8")
    compiled = compile_standard(
        {
            "language": "Solidity",
            "sources": {"HashRegistry.sol": {"content": source}},
            "settings": {
                "outputSelection": {
                    "*": {"*": ["abi", "evm.bytecode.object"]},
                }
            },
        },
        solc_version=solc_version,
    )

    contract_data = compiled["contracts"]["HashRegistry.sol"]["HashRegistry"]
    artifact = {
        "contract_name": "HashRegistry",
        "abi": contract_data["abi"],
        "bytecode": contract_data["evm"]["bytecode"]["object"],
        "solc_version": solc_version,
    }

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    import json

    (ARTIFACTS_DIR / "HashRegistry.json").write_text(
        json.dumps(artifact, indent=2), encoding="utf-8"
    )
    return artifact


def load_artifact() -> dict:
    """Load a previously compiled artifact, compiling first if missing."""
    artifact_path = ARTIFACTS_DIR / "HashRegistry.json"
    if artifact_path.exists():
        import json

        return json.load(artifact_path.open(encoding="utf-8"))
    return compile_contract()
