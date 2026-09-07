<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f2027,50:2c5364,100:00c9ff&height=220&section=header&text=Face-Match%20Discovery&fontSize=42&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=%2B%20Blockchain%20Verification%20%7C%20HH%20Goa%202026%20%E2%80%94%20Shortlisting%20Task%203&descAlignY=58&descSize=18" width="100%"/>

<br/>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&duration=2800&pause=900&color=00C9FF&center=true&vCenter=true&width=760&lines=Discover+public+photo+matches+for+a+given+face;Anchor+a+canonical+SHA-256+hash+on+Polygon+PoS+Amoy;Independently+re-verify+with+ON_CHAIN+%2B+SOURCE+checks)](https://git.io/typing-svg)

<br/>

![Python](https://img.shields.io/badge/Python-3.11.15-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Polygon](https://img.shields.io/badge/Polygon-Amoy%20Testnet-8247E5?style=for-the-badge&logo=polygon&logoColor=white)
![web3](https://img.shields.io/badge/web3.py-8.0.0-F16822?style=for-the-badge&logo=ethereum&logoColor=white)
![Status](https://img.shields.io/badge/Status-Submission%20Ready-brightgreen?style=for-the-badge)

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=6,11,20&height=3&width=1000" width="100%"/>

</div>

# Face-Match Discovery + Blockchain Verification

**HH Goa 2026 — Shortlisting Task 3**

A Python pipeline that discovers publicly posted photos matching a given face,
anchors a canonical SHA-256 hash of the match on **Polygon PoS Amoy testnet**,
and supports independent **ON_CHAIN** and **SOURCE** re-verification.

> **Naming:** This is **face-match discovery**, not legal/biometric identity
> verification. A successful match means an image resembling the input face was
> found at a public URL — not "this person is definitely X."

---

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=transparent&color=auto&height=45&section=header&text=HH%20Goa%20Task%203%20Mapping&fontSize=20&fontColor=00C9FF&fontAlignY=70" width="100%"/>
</div>

## HH Goa Task 3 mapping

| Task requirement | Implementation |
|------------------|----------------|
| Input face image | `--input` local photo |
| Face detection + encoding | `src/face/` (`face_recognition`, 128-d embeddings) |
| Genuine reverse-image search | SearchApi.io Google Lens (`src/search/searchapi_client.py`) |
| Real social-media post match | Domain allowlist + face re-verification (`src/search/match_finder.py`) |
| Hash / fingerprint evidence | Canonical JSON payload + SHA-256 (`src/blockchain/hasher.py`) |
| Blockchain write | `HashRegistry.storeHash()` on Polygon Amoy (`src/blockchain/upload.py`) |
| Blockchain re-verification | ON_CHAIN + SOURCE (`src/blockchain/verify.py`) |
| README + screen recording | This document + unedited `main.py` run |

No web frontend. Testnet only (not mainnet).

---

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=transparent&color=auto&height=45&section=header&text=Architecture&fontSize=20&fontColor=00C9FF&fontAlignY=70" width="100%"/>
</div>

## Architecture

```
Input image (--input) + public URL (--image-url)
    → Face detection + encoding
    → SearchApi.io reverse-image search
    → Social domain filtering (allowlist)
    → Face re-verification (Euclidean distance)
    → Canonical payload + SHA-256
    → Polygon Amoy HashRegistry (storeHash)
    → ON_CHAIN verification (verifyHash)
    → SOURCE re-verification (re-fetch image, re-hash)
```

Outputs: `data/output/match_result.json`, `data/output/verification_log.json`

---

## Components

| Path | Role |
|------|------|
| `main.py` | End-to-end orchestrator |
| `src/face/detect.py` | Largest-face detection |
| `src/face/encode.py` | Embeddings + `face_distance()` |
| `src/search/searchapi_client.py` | SearchApi.io Google Lens client |
| `src/search/match_finder.py` | Allowlist filter, download, re-verify |
| `src/blockchain/hasher.py` | Canonical payload + SHA-256 |
| `src/blockchain/chain_config.py` | Web3 setup, Amoy chain ID (80002), PoA middleware |
| `src/blockchain/contract/compile.py` | `py-solc-x` contract compiler (`solc 0.8.20`) |
| `src/blockchain/deploy.py` | Deploy HashRegistry to Amoy |
| `src/blockchain/upload.py` | `storeHash()` |
| `src/blockchain/verify.py` | ON_CHAIN + SOURCE checks |
| `src/blockchain/contract/HashRegistry.sol` | On-chain hash registry |
| `scripts/calibrate_threshold.py` | Threshold calibration on real sample images |
| `scripts/run_pipeline.sh` | Convenience bash runner script |

---

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=transparent&color=auto&height=45&section=header&text=Installation&fontSize=20&fontColor=00C9FF&fontAlignY=70" width="100%"/>
</div>

## Installation

**Tested environment:** Python 3.11.15 (64-bit), Windows AMD64, `.venv-fresh-test`

### Linux / macOS

> **System Prerequisites:** Compiling `dlib` on Unix requires `cmake` and C/C++ build tools:
> - Debian/Ubuntu: `sudo apt-get install -y cmake build-essential libopenblas-dev liblapack-dev`
> - macOS: `brew install cmake`

```bash
cd face-match-verify
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows (important — avoid dlib source build)

Official `dlib` fails to compile from source on Windows without full Visual Studio C++ toolchains. Use **dlib-bin**:

```powershell
cd face-match-verify
python -m venv .venv-fresh-test
.\.venv-fresh-test\Scripts\Activate.ps1

# Step 1: Install pre-compiled Windows dlib binary wheel and face models
pip install dlib-bin==20.0.1
pip install face-recognition==1.3.0 --no-deps
pip install face-recognition-models Click numpy==2.4.6 Pillow==12.3.0 setuptools==69.5.1

# Step 2: Install remaining dependencies with --no-deps to prevent triggering official dlib compilation
pip install -r requirements.txt --no-deps
```

Do **not** run `pip install face-recognition` without `--no-deps` on Windows —
pip may attempt to build official dlib from source.

**Import smoke test:**

```bash
python -c "import dlib; import face_recognition; import face_recognition_models; print('dlib:', dlib.__version__); print('face_recognition: OK'); print('face_recognition_models: OK')"
```

---

## Environment variables

Copy `.env.example` → `.env` (never commit `.env`):

| Variable | Description |
|----------|-------------|
| `SEARCHAPI_KEY` | [SearchApi.io](https://www.searchapi.io/) key (Google Lens engine) |
| `RPC_URL` | Polygon **Amoy** HTTPS RPC (Alchemy, Infura, etc.) |
| `PRIVATE_KEY` | Test wallet private key |
| `CONTRACT_ADDRESS` | Deployed HashRegistry address |

See [scripts/fund_test_wallet.md](scripts/fund_test_wallet.md) for faucet + MetaMask setup.

**Deployed contract (this project):** `0x46077C47ab22Aa84b4feb3f7165A75dfbAA29906`

---

## Face recognition methodology

- Library: [`face_recognition`](https://github.com/ageitgey/face_recognition) (128-d embeddings)
- **Input face:** largest face in the local `--input` image
- **Candidate face:** first detected face in each downloaded candidate image
- **Metric:** Euclidean `face_distance()` — **lower = closer match**
- **Not used:** cosine similarity (misleadingly high on different people in our tests)
- **Threshold:** `0.53` (calibrated via `scripts/calibrate_threshold.py` on real photos)
- **Accept rule:** `face_distance <= 0.53`

---

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=transparent&color=auto&height=45&section=header&text=Canonical%20Payload%20Schema&fontSize=20&fontColor=00C9FF&fontAlignY=70" width="100%"/>
</div>

## Canonical payload schema

Deterministic JSON (sorted keys before hashing):

```json
{
  "source_url": "https://x.com/angiegomeza/status/1487496452762972163",
  "matched_image_hash": "9a6479afbc68ce220cfca6f237a8d10e24014890c1293d1503806b2b77562cc5",
  "face_distance": "0.4765",
  "timestamp": "2026-09-07T02:39:29Z"
}
```

- `source_url`: allowlisted social post URL (`link` from SearchApi candidate)
- `matched_image_hash`: SHA-256 hex of raw downloaded image bytes
- `face_distance`: normalized 4-decimal **string** (`normalize_face_distance()`, Euclidean distance)
- `timestamp`: UTC ISO-8601, generated once at match time

**Payload hash:**
```python
hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
```
Alphabetical key sorting ensures deterministic hashing regardless of dictionary insertion order.
Final submission payload hash: `0e6691236b05cae6a4983ba71c20c030701accf53934b01602131bec53247677`

> **Schema note:** Earlier debugging runs used the field name `face_similarity_score`.
> The submission schema uses `face_distance`. Renaming changes the canonical JSON and therefore
> produces a distinct payload hash. The golden-baseline and final-submission transactions
> correspond to their respective schemas (see details below).

---

## Polygon Amoy contract

**Network:** Polygon PoS Amoy, chain ID `80002`

**HashRegistry.sol:**

- `storeHash(bytes32 _hash)` — stores `{ dataHash, submitter, timestamp }`
- `verifyHash(bytes32 _hash)` → `(bool exists, uint256 timestamp)`
- Overwrite-on-resubmit: storing the same hash again updates metadata (documented limitation)

**Deploy (once):**

```bash
python -m src.blockchain.deploy
```

**Upload hash only** (stores digest, not the JSON payload):

```bash
python -m src.blockchain.upload <payload_hash_hex>
```

---

## Verification

### ON_CHAIN (read-only)

Calls `verifyHash(payload_hash)` on the deployed contract.

- `FOUND` / `MISSING`
- Returns on-chain storage timestamp when found
- Does not inspect the live image

### SOURCE

1. Re-fetch `match.matched_image_source_url`
2. Recompute `matched_image_hash` from fresh bytes
3. Rebuild canonical payload reusing **original** `timestamp` and `face_distance`
4. Recompute payload hash and compare to `payload_hash`

Outcomes: `MATCH` / `NO MATCH` / `UNVERIFIABLE`

---

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=transparent&color=auto&height=45&section=header&text=Running%20the%20Pipeline&fontSize=20&fontColor=00C9FF&fontAlignY=70" width="100%"/>
</div>

## Running the pipeline

SearchApi.io requires a **public URL** for the same photo as `--input`:

```bash
python main.py \
  --input data/sample_input/person_a_1.jpg \
  --image-url https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/biden.jpg
```

**Windows PowerShell:**

```powershell
python main.py --input "data\sample_input\person_a_1.jpg" --image-url "https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/biden.jpg"
```

**Linux / macOS / Git Bash runner script:**

```bash
IMAGE_URL="https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/biden.jpg" ./scripts/run_pipeline.sh
```

Expected successful stages:

```
[1/6] Encoding face
[2/6] Reverse-image search (N candidates)
[3/6] Filtering + face re-verification → Status: match
[4/6] Canonical hash
[5/6] Uploading hash to Polygon Amoy
[6/6] ON_CHAIN: FOUND  SOURCE: MATCH
```

Do **not** use `--skip-blockchain` or `--skip-verify` for the submission demo.

---

## Testing

```bash
python -m pytest -q
```

Or run individually:

```bash
python tests/test_face.py
python tests/test_search.py
python tests/test_blockchain.py
```

Tests use real network downloads where noted (GitHub-hosted images).

---

## Output artifacts

| File | Contents | Generated By |
|------|----------|--------------|
| `data/output/match_result.json` | Match metadata, canonical payload, payload hash, blockchain tx | `main.py` (pipeline run) |
| `data/output/verification_log.json` | ON_CHAIN + SOURCE verification results | `main.py` (pipeline run) |
| `data/output/deploy_info.json` | Contract deploy metadata (address, tx, block, solc version) | `deploy.py` (one-time setup) |

No secrets are written to these files.

---

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=transparent&color=auto&height=45&section=header&text=Example%20Runs%20%26%20Transactions&fontSize=20&fontColor=00C9FF&fontAlignY=70" width="100%"/>
</div>

## Example runs & transactions

### Historical debugging transaction — not the final submission result

This transaction is preserved for development/audit history only. The final submission result is documented in the section below.

Used during development to validate pipeline mechanics. Canonical field was `face_similarity_score`.

| Field | Value |
|-------|-------|
| Payload hash | `b0009c1d68acc29a2b997364bb186da94ef383d819e8ac5729c181e4cb02acb3` |
| Tx hash | `0f05080d1b2ba7f5952c1459caa7dec93a21f6b6bc2eec32035fddeaaa1db48a` |
| Block | `46926971` |
| Explorer | [amoy.polygonscan.com](https://amoy.polygonscan.com/tx/0x0f05080d1b2ba7f5952c1459caa7dec93a21f6b6bc2eec32035fddeaaa1db48a) |

### Final submission run (canonical schema with `face_distance`)

Production submission run confirming end-to-end correctness with the normalized `face_distance` field.

| Field | Value |
|-------|-------|
| Target Post URL | [x.com/angiegomeza/status/1487496452762972163](https://x.com/angiegomeza/status/1487496452762972163) |
| Matched Image URL | `https://pbs.twimg.com/amplify_video_thumb/1487171137444458501/img/qpRnuPxfSmXcZR4j.jpg` |
| Face distance | `0.4765` (raw: `0.47647`, accepted under threshold `0.53`) |
| Matched Image SHA-256 | `9a6479afbc68ce220cfca6f237a8d10e24014890c1293d1503806b2b77562cc5` |
| Canonical Payload Hash | `0e6691236b05cae6a4983ba71c20c030701accf53934b01602131bec53247677` |
| Tx hash | `1fbd549f2850a0a5cfd07094e6c7df5f4a98472f7d36d0bc79d16355136333f5` |
| Block | `46930330` |
| Contract | `0x46077C47ab22Aa84b4feb3f7165A75dfbAA29906` |
| Explorer | [amoy.polygonscan.com](https://amoy.polygonscan.com/tx/0x1fbd549f2850a0a5cfd07094e6c7df5f4a98472f7d36d0bc79d16355136333f5) |
| ON_CHAIN verification | `FOUND` (timestamp: `1788748772`) |
| SOURCE verification | `MATCH` (`original_payload_hash == recomputed_payload_hash`) |

**Contract (both runs):** `0x46077C47ab22Aa84b4feb3f7165A75dfbAA29906`

---

## Supported social platforms

Allowlist only (not exhaustive web coverage):

- `instagram.com` / `www.instagram.com`
- `facebook.com` / `www.facebook.com`
- `twitter.com` / `x.com` / `www.x.com`
- `linkedin.com` / `www.linkedin.com`
- `reddit.com` / `www.reddit.com`

Candidates on other domains or unlisted subdomains (such as mobile `m.facebook.com` or `mobile.twitter.com`) are skipped by design.

### Media resolution precedence
SearchApi.io candidate image fields may be URL strings **or** objects such as `{ "link": "..." }`. The pipeline normalizes these fields and prioritizes the candidate's `image` field over its `thumbnail` field when available:
```python
image_source_url = _extract_media_url(c.get("image") or c.get("thumbnail"))
```

---

## Security / secrets

- Never commit `.env`, private keys, or API keys
- Use a dedicated testnet wallet
- Rotate SearchApi.io keys if exposed during development
- Demo only with your own or consenting subjects' photos

---

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=transparent&color=auto&height=45&section=header&text=Known%20Limitations&fontSize=20&fontColor=00C9FF&fontAlignY=70" width="100%"/>
</div>

## Known limitations

1. **Discovery, not identification** — does not prove legal identity or account ownership.
2. **Allowlist scope** — five platform families only; mobile subdomains (e.g. `m.facebook.com`) excluded.
3. **Calibration** — threshold 0.53 from a small public photo set; not guaranteed on all faces.
4. **Multi-face candidate images** — uses the **first** detected face in a candidate image for re-verification. If the target person is not the first detected face, the candidate may be rejected. A future enhancement could compare against all detected faces.
5. **SearchApi.io** — requires public image hosting; API quota on free tier.
6. **Ephemeral CDN URLs** — matched image URLs may expire → SOURCE `UNVERIFIABLE` while ON_CHAIN still `FOUND`.
7. **Platform blocks and HTML gates** — Instagram/Facebook may return HTTP 403 or HTML login wrappers (raising `cannot identify image file`); skipped gracefully with logged reasons.
8. **Overwrite-on-resubmit** — same hash stored twice updates on-chain metadata.
9. **Input vs URL not validated** — `--input` and `--image-url` must be the same photo (operator responsibility; the pipeline does not independently verify image URL identity before query).
10. **Testnet only** — no production security audit.
11. **Test fixture dependency** — unit tests (`test_search.py`) require threshold sample fixtures in `data/calibration/threshold_samples/` (tracked in repository).

---

## Reproducibility

- Pin: `web3==8.0.0`, `face_recognition==1.3.0`, `numpy==2.4.6`
- Windows: use `dlib-bin==20.0.1` (see Installation)
- Amoy chain ID `80002` enforced in `chain_config.py`
- PoA middleware required (`ExtraDataToPOAMiddleware`)

---

## License / submission

Built for HH Goa 2026 Shortlisting Task 3. Rotate API keys before final submission.

<div align="center">
<br/>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:00c9ff,50:2c5364,100:0f2027&height=150&section=footer" width="100%"/>

</div>
