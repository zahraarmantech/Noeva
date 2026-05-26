# NOEVA

**Novel Obfuscated Embedding Vector Architecture**

Privacy-preserving semantic search via multi-channel modular arithmetic. Search sensitive documents by meaning without exposing content — not to the database, not to the server, not even to the key holder.

**Patent Pending** · US Provisional Patent Filed 2026

---

## What It Does

Standard semantic search stores document embeddings in plain vectors. Anyone with database access can cluster documents by topic and infer content without reading a single word.

NOEVA transforms embeddings into modular barcodes: masked, quantized, and distributed across prime-modular channels. The result looks like random noise to any observer — but search still works.

```
Standard search:  embedding → cosine similarity → ranked results
                  ⚠ Embeddings leak semantic structure

NOEVA search:     embedding → modular barcode → encrypted distance → ranked results
                  ✓ Barcodes reveal nothing without the key
```

## Results

All numbers verified on real data. No synthetic benchmarks.

| Benchmark | Corpus | Quality (% of cosine) |
|-----------|--------|-----------------------|
| MSMARCO | 626,906 passages | 98.2% |
| SciFact | 5,183 docs | 95.7% |
| NFCorpus | 3,633 docs | 89.9% |
| STS-B | 1,379 pairs | 100.1% |

| Comparison | MRR@10 | Encrypted |
|------------|--------|-----------|
| Cosine (float32) | .530 | No |
| Binary quantization | .514 | No |
| Product quantization | .520 | No |
| **NOEVA (ours)** | **.528** | **Yes** |

**8× faster** than CKKS FHE on identical hardware (5ms vs 39ms per comparison).

Three embedding models tested. Five languages verified. Eight security tests passed.

## Quick Start

```python
from noeva_search import ModularBarcodeSystem

# Initialize
system = ModularBarcodeSystem(key="your-secret-key", n_channels=200)

# Fit on corpus embeddings
system.fit(corpus_embeddings)

# Encode documents
barcodes = system.encode(corpus_embeddings, doc_ids)

# Encode query
query_bc = system.encode_query(query_embedding)

# Compare (key holder only)
distance = system.compare(query_bc, barcodes[0])
```

## How It Works

1. **Decompose**: Project embedding onto 200 PCA channels
2. **Quantize**: Convert each channel to integer (0–49)
3. **Mask**: Apply rejection-sampled salt + wave interference per document
4. **Store**: Keep only modular residues (mod prime)
5. **Search**: Compare in modular space — raw embedding never reconstructed

Key design rule: all primes must exceed the bin count for injective modular reduction.

## Security

Eight independent attack vectors tested:

| Attack | Result | Status |
|--------|--------|--------|
| IND-CPA indistinguishability | p = 0.48 | Pass |
| Statistical correlation | ρ = 0.10 | Pass |
| Entropy analysis | 100% | Pass |
| Per-channel leakage | \|r\| = 0.30 | Pass |
| Key recovery | 1.0% vs 1.9% baseline | Pass |
| Chosen-plaintext | ρ = 0.00 | Pass |
| Timing side-channel | p = 1.00 | Pass |
| CRT reconstruction | \|r\| = 0.01 | Pass |

Formal proofs under PRF assumption (HMAC-SHA256) provided in `paper/proof.pdf`.

**Threat model**: Protected against unauthorized database observers. The key holder computes distances but never reconstructs raw embeddings. MDS geometry recovery by key holder is mitigated via log-transform (ρ reduced from 0.63 to 0.35).

## Project Structure

```
noeva-search/
├── README.md
├── noeva_search.py          # Core system (530 lines, self-testing)
├── demo/
│   └── encrypted_search_demo.jsx   # Interactive visual demo
├── paper/
│   ├── Lightweight_Encrypted_Semantic_Search.pdf
│   └── Formal_Security_Proof.pdf
└── LICENSE
```

## Run Self-Test

```bash
python noeva_search.py
```

Runs 8 security tests, validates prime selection, tests access pattern guard.

## Cite

```
@misc{arman2026noeva,
  title={Lightweight Encrypted Semantic Search via Multi-Channel Modular Signaling},
  author={Zahra Arman},
  year={2026},
  note={US Provisional Patent Filed. Available at github.com/zahraarmantech/noeva-search}
}
```

## License

MIT License. The method described is covered by a pending US provisional patent.

## Author

**Zahra Arman** — Independent Researcher, Plano, TX

zahra.arman.tech@gmail.com
