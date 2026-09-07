# Fund Your Polygon PoS Amoy Testnet Wallet

You need a small amount of testnet POL/MATIC to deploy `HashRegistry` and call
`storeHash()`. This costs nothing real — Amoy is Polygon's public testnet.

## Network

| Field | Value |
|-------|-------|
| Network name | **Polygon PoS Amoy** |
| Chain ID | `80002` |
| Currency symbol | POL (shown as MATIC in some wallets) |
| Block explorer | https://amoy.polygonscan.com |

Do **not** use Polygon mainnet for this project.

## 1. Create / import a wallet

Use MetaMask (or any EVM wallet). **Use a dedicated test wallet** — never
reuse a mainnet wallet's private key.

Export the private key into your local `.env` as `PRIVATE_KEY`. Never commit
or paste it in chat.

## 2. Add Polygon Amoy to MetaMask

| Field | Value |
|-------|-------|
| Network name | Polygon Amoy |
| RPC URL | Your provider endpoint (see step 4) |
| Chain ID | `80002` |
| Currency symbol | `MATIC` or `POL` |
| Block explorer | https://amoy.polygonscan.com |

## 3. Get free testnet POL

1. Go to https://faucet.polygon.technology
2. Select **Polygon Amoy**
3. Paste your wallet address
4. Complete verification
5. Wait 1–2 minutes; balance should show enough for a few transactions

If the official faucet is dry, search for "Polygon Amoy faucet" — community
faucets exist. You only need enough for deploy + one or two `storeHash` calls.

## 4. Configure RPC in `.env`

Create `.env` from `.env.example`. Set `RPC_URL` to your provider's **Amoy**
endpoint — do not hard-code credentials in this repo.

Examples (replace with your own key):

- Alchemy: create an app → enable **Polygon Amoy** → copy HTTPS URL
- Infura: create a project → enable **Polygon Amoy** → copy HTTPS URL

```env
RPC_URL=https://polygon-amoy.g.alchemy.com/v2/YOUR_KEY
PRIVATE_KEY=0xYOUR_TEST_WALLET_KEY
SEARCHAPI_KEY=your_searchapi_key
CONTRACT_ADDRESS=0x...   # after deploy
```

## 5. Deploy and run

Contract deploy (once):

```bash
python -m src.blockchain.deploy
```

Copy the printed `CONTRACT_ADDRESS` into `.env`.

Full pipeline:

```bash
python main.py \
  --input data/sample_input/person_a_1.jpg \
  --image-url https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/biden.jpg
```

Verify transactions on https://amoy.polygonscan.com using the tx hash printed
by deploy or upload.

## Deployed contract (this project)

The HashRegistry for this submission was deployed to Amoy at:

`0x46077C47ab22Aa84b4feb3f7165A75dfbAA29906`

Set that address as `CONTRACT_ADDRESS` in your `.env` if reusing the same
deployment. Deploy your own copy only if you need a fresh registry.
