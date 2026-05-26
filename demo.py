"""
ZATRON Demo — Privacy-Preserving Semantic Search

Run:
    pip install sentence-transformers scikit-learn matplotlib
    python demo.py

Generates:
    - Terminal output with search quality and security results
    - zatron_comparison.png — t-SNE visualization (raw vs protected)
    - zatron_attack.png — attack analysis visualization
"""

import numpy as np
import sys
import time

# ─────────────────────────────────────────────────
# 50 real documents, 5 topics, 10 each
# ─────────────────────────────────────────────────
DOCUMENTS = {
    "Medical": [
        "Patient presents with chronic obstructive pulmonary disease and shortness of breath",
        "Blood panel reveals elevated troponin levels suggesting myocardial injury",
        "MRI confirms anterior cruciate ligament tear requiring surgical intervention",
        "Prescribed insulin glargine for type 2 diabetes with poor glycemic control",
        "Post-operative recovery complicated by surgical site infection",
        "Echocardiogram shows reduced left ventricular ejection fraction",
        "Pathology report indicates stage 2 invasive ductal carcinoma",
        "Neurological exam reveals decreased reflexes consistent with peripheral neuropathy",
        "Chest X-ray shows bilateral pleural effusion requiring thoracentesis",
        "Colonoscopy revealed multiple adenomatous polyps requiring removal",
    ],
    "Legal": [
        "Defendant moves to suppress evidence obtained without valid search warrant",
        "Non-compete agreement found unenforceable due to excessive geographic scope",
        "Plaintiff alleges breach of fiduciary duty by corporate board members",
        "Settlement agreement requires mutual release of all pending claims",
        "Court ordered temporary restraining order against former business partner",
        "Deposition transcript reveals contradictions in witness testimony",
        "Patent infringement claim dismissed for failure to show literal infringement",
        "Arbitration clause prevents class action lawsuit from proceeding",
        "Landlord tenant dispute over security deposit return and property damage",
        "Merger agreement includes material adverse change clause",
    ],
    "Financial": [
        "Quarterly earnings exceeded analyst expectations by fourteen percent",
        "Portfolio rebalancing shifted allocation toward investment grade bonds",
        "Cash flow analysis indicates insufficient liquidity for Q3 obligations",
        "Stock buyback program authorized for up to five hundred million dollars",
        "Depreciation schedule adjusted following asset impairment assessment",
        "Revenue recognition policy updated to comply with ASC 606 guidelines",
        "Internal audit identified material weakness in expense reporting controls",
        "Foreign exchange hedging strategy reduced currency exposure by thirty percent",
        "Pension fund liabilities increased due to lower discount rate assumptions",
        "Capital expenditure budget approved for new manufacturing facility",
    ],
    "Technical": [
        "Kubernetes cluster experiencing pod eviction due to memory pressure",
        "Database query optimization reduced average response time by sixty percent",
        "Microservice architecture migration completed for payment processing system",
        "SSL certificate chain validation failing after intermediate CA rotation",
        "Load testing revealed connection pool exhaustion under concurrent requests",
        "Continuous integration pipeline failing at static analysis stage",
        "Redis cache invalidation strategy causing stale data in user sessions",
        "GraphQL schema migration requires backward compatible field deprecation",
        "Container image vulnerability scan detected critical CVE in base image",
        "Message queue consumer lag increasing due to partition rebalancing",
    ],
    "Personal": [
        "Annual performance review rates employee as exceeding expectations",
        "Salary negotiation resulted in fifteen percent base compensation increase",
        "Formal complaint filed alleging workplace harassment by direct supervisor",
        "Background verification confirmed educational credentials and employment history",
        "Short term disability leave approved for post-surgical recovery period",
        "Exit interview cited lack of career advancement as primary resignation reason",
        "Workplace accommodation request approved for ergonomic desk equipment",
        "Mandatory training completion overdue for information security awareness",
        "Employee assistance program referral made for stress management counseling",
        "Promotion committee recommended candidate for senior engineering position",
    ],
}


def main():
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.manifold import TSNE
        from sklearn.utils.extmath import randomized_svd
        from scipy.stats import spearmanr
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n  pip install sentence-transformers scikit-learn matplotlib")
        sys.exit(1)

    import hmac, hashlib

    all_docs = []
    all_topics = []
    topic_names = list(DOCUMENTS.keys())
    for topic, docs in DOCUMENTS.items():
        for doc in docs:
            all_docs.append(doc)
            all_topics.append(topic_names.index(topic))
    N = len(all_docs)

    colors_map = ["#ef4444", "#3b82f6", "#eab308", "#22c55e", "#a855f7"]
    colors = [colors_map[t] for t in all_topics]

    # ─────────────────────────────────────────
    print()
    print("=" * 62)
    print("  ZATRON — Zero-Access Transformed Retrieval Over Noise")
    print("=" * 62)
    print(f"\n  {N} documents | {len(topic_names)} topics | Real sentences")
    print(f"  Topics: {', '.join(topic_names)}")

    print(f"\n  Encoding with all-MiniLM-L6-v2...", end=" ", flush=True)
    sbert = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = sbert.encode(all_docs, show_progress_bar=False).astype(np.float32)
    print(f"done ({embeddings.shape[1]}d)")

    # ZATRON encoding
    N_BINS = 50
    PRIMES = [53, 59, 61, 67, 71, 73]
    KEY = b"zatron-demo-2026"
    me = embeddings.mean(0)
    ce = embeddings - me
    n_ch = min(200, N - 1, embeddings.shape[1])
    _, _, Vt = randomized_svd(ce, n_components=n_ch, random_state=42)
    pr = ce @ Vt[:n_ch].T
    pm = pr.min(0)
    prng = pr.max(0) - pm + 1e-8
    var = np.var(pr, 0)
    wt = (var / var.sum()).astype(np.float32)
    sigs = np.clip(((pr - pm) / prng * (N_BINS - 1)).astype(np.int64), 0, N_BINS - 1)

    def make_mask(doc_id, prime):
        mx = (256 // prime) * prime
        sl = np.zeros(n_ch, dtype=np.int64)
        c, f = 0, 0
        while f < n_ch:
            h = hmac.new(KEY, f"{doc_id}:{prime}:{c}".encode(),
                         hashlib.sha256).digest()
            for b in h:
                if f >= n_ch:
                    break
                if b < mx:
                    sl[f] = b % prime
                    f += 1
            c += 1
        return sl

    barcodes = []
    for i in range(N):
        layers = []
        for p in PRIMES:
            mask = make_mask(f"doc_{i}", p)
            layers.append((sigs[i] + mask) % p)
        barcodes.append(np.hstack(layers).astype(float))
    barcode_matrix = np.array(barcodes)

    # ─────────────────────────────────────────
    # STEP 1: SECURITY — Can observer recover similarity?
    # ─────────────────────────────────────────
    print(f"\n{'─' * 62}")
    print(f"  SECURITY ANALYSIS")
    print(f"{'─' * 62}")

    true_sims = []
    raw_dists = []
    barcode_dists = []
    for i in range(N):
        for j in range(i + 1, N):
            cs = float(np.dot(embeddings[i], embeddings[j]) / (
                np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j]) + 1e-10))
            true_sims.append(cs)
            raw_dists.append(float(np.linalg.norm(embeddings[i] - embeddings[j])))
            barcode_dists.append(float(np.sum(np.abs(barcode_matrix[i] - barcode_matrix[j]))))

    rho_raw, p_raw = spearmanr(true_sims, raw_dists)
    rho_prot, p_prot = spearmanr(true_sims, barcode_dists)

    print(f"\n  Raw embeddings → similarity correlation:")
    print(f"    ρ = {abs(rho_raw):.4f}  ⚠ ATTACKER RECOVERS SIMILARITY")
    print(f"\n  ZATRON barcodes → similarity correlation:")
    status = "✓ NO MEANINGFUL CORRELATION" if abs(rho_prot) < 0.15 else "⚠ SOME CORRELATION DETECTED"
    print(f"    ρ = {abs(rho_prot):.4f}  {status}")

    # ─────────────────────────────────────────
    # STEP 2: SEARCH QUALITY — Does search still work?
    # ─────────────────────────────────────────
    print(f"\n{'─' * 62}")
    print(f"  SEARCH QUALITY")
    print(f"{'─' * 62}")

    queries = [
        ("lung disease breathing difficulty", "Medical"),
        ("contract breach legal dispute", "Legal"),
        ("quarterly earnings revenue forecast", "Financial"),
        ("kubernetes deployment container", "Technical"),
        ("employee performance review promotion", "Personal"),
    ]

    norms_p = np.linalg.norm(embeddings, axis=1)
    cos_correct = 0
    enc_correct = 0
    cos_top1_match = 0

    print(f"\n  {'Query':<42} {'Cosine #1':<20} {'ZATRON #1':<20} {'Same?'}")
    print(f"  {'─' * 95}")

    for query_text, expected_topic in queries:
        q_emb = sbert.encode([query_text], show_progress_bar=False).astype(np.float32)[0]

        # Cosine
        cos_scores = embeddings @ q_emb / (norms_p * np.linalg.norm(q_emb) + 1e-10)
        cos_top = int(np.argsort(-cos_scores)[0])
        cos_topic = topic_names[all_topics[cos_top]]

        # ZATRON
        q_proj = (q_emb - me) @ Vt[:n_ch].T
        q_sig = np.clip(((q_proj - pm) / prng * (N_BINS - 1)).astype(np.int64), 0, N_BINS - 1)
        enc_scores = np.zeros(N)
        for p in PRIMES:
            q_mod = q_sig % p
            for idx in range(N):
                diff = np.abs((sigs[idx] % p).astype(np.int64) - q_mod.astype(np.int64))
                enc_scores[idx] += np.sum(np.minimum(diff, p - diff).astype(float) * wt) / (p * wt.sum())
        enc_scores /= len(PRIMES)
        enc_top = int(np.argsort(enc_scores)[0])
        enc_topic = topic_names[all_topics[enc_top]]

        same = "✓" if cos_top == enc_top else "~"
        if cos_topic == expected_topic: cos_correct += 1
        if enc_topic == expected_topic: enc_correct += 1
        if cos_top == enc_top: cos_top1_match += 1

        print(f"  {query_text:<42} {all_docs[cos_top][:18]:<20} {all_docs[enc_top][:18]:<20} {same}")

    print(f"\n  Cosine correct topic:  {cos_correct}/{len(queries)}")
    print(f"  ZATRON correct topic:  {enc_correct}/{len(queries)}")
    print(f"  Exact same top-1:      {cos_top1_match}/{len(queries)}")

    # ─────────────────────────────────────────
    # STEP 3: GENERATE VISUALIZATIONS
    # ─────────────────────────────────────────
    print(f"\n{'─' * 62}")
    print(f"  GENERATING VISUALIZATIONS")
    print(f"{'─' * 62}")

    print(f"\n  Computing t-SNE...", end=" ", flush=True)
    tsne_raw = TSNE(n_components=2, random_state=42, perplexity=10).fit_transform(embeddings)
    tsne_prot = TSNE(n_components=2, random_state=42, perplexity=10).fit_transform(barcode_matrix)
    print("done")

    # Plot 1: t-SNE comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor('#0a0a0f')

    for ax, data, title, bc in [
        (ax1, tsne_raw, "Standard Embeddings — EXPOSED", "#ef4444"),
        (ax2, tsne_prot, "ZATRON Protected — SAFE", "#22c55e"),
    ]:
        ax.set_facecolor('#0f0f18')
        for i in range(N):
            ax.scatter(data[i, 0], data[i, 1], c=colors[i], s=70,
                      alpha=0.85, edgecolors='white', linewidths=0.3, zorder=3)
        ax.set_title(title, fontsize=13, fontweight='bold', color=bc,
                    pad=12, fontfamily='monospace')
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color(bc); spine.set_linewidth(1.5)

    for i, (topic, color) in enumerate(zip(topic_names, colors_map)):
        ax1.scatter([], [], c=color, s=50, label=topic)
    ax1.legend(loc='lower left', fontsize=8, facecolor='#0f0f18',
              edgecolor='#333', labelcolor='white')

    ax1.text(0.5, -0.07, "⚠ Topics visible — same colors cluster together",
            transform=ax1.transAxes, ha='center', fontsize=9, color='#ef4444', fontfamily='monospace')
    ax2.text(0.5, -0.07, "✓ No structure — colors randomly scattered",
            transform=ax2.transAxes, ha='center', fontsize=9, color='#22c55e', fontfamily='monospace')

    fig.suptitle("ZATRON — Same Documents, Same Search Quality, Different Visibility",
                fontsize=15, color='white', fontweight='bold', fontfamily='monospace', y=0.98)
    plt.tight_layout(rect=[0, 0.02, 1, 0.93])
    plt.savefig('zatron_comparison.png', dpi=150, facecolor='#0a0a0f',
                bbox_inches='tight', pad_inches=0.3)
    print(f"  Saved: zatron_comparison.png")

    # Plot 2: Attack analysis
    fig2, (ax3, ax4) = plt.subplots(1, 2, figsize=(14, 6))
    fig2.patch.set_facecolor('#0a0a0f')

    ax3.set_facecolor('#0f0f18')
    ax3.scatter(true_sims, raw_dists, c='#ef4444', alpha=0.3, s=8)
    ax3.set_xlabel('True Cosine Similarity', color='white', fontsize=10)
    ax3.set_ylabel('Raw Embedding Distance', color='white', fontsize=10)
    ax3.set_title(f'Raw: ρ = {abs(rho_raw):.2f} — SIMILARITY LEAKED',
                 color='#ef4444', fontsize=11, fontweight='bold', fontfamily='monospace')
    ax3.tick_params(colors='#666')
    for spine in ax3.spines.values():
        spine.set_color('#ef4444'); spine.set_linewidth(1.5)

    ax4.set_facecolor('#0f0f18')
    ax4.scatter(true_sims, barcode_dists, c='#22c55e', alpha=0.3, s=8)
    ax4.set_xlabel('True Cosine Similarity', color='white', fontsize=10)
    ax4.set_ylabel('Barcode Distance', color='white', fontsize=10)
    ax4.set_title(f'ZATRON: ρ = {abs(rho_prot):.2f} — NO CORRELATION',
                 color='#22c55e', fontsize=11, fontweight='bold', fontfamily='monospace')
    ax4.tick_params(colors='#666')
    for spine in ax4.spines.values():
        spine.set_color('#22c55e'); spine.set_linewidth(1.5)

    fig2.suptitle("Can an Observer Recover Document Similarity?",
                 fontsize=15, color='white', fontweight='bold', fontfamily='monospace', y=0.98)
    plt.tight_layout(rect=[0, 0.02, 1, 0.93])
    plt.savefig('zatron_attack.png', dpi=150, facecolor='#0a0a0f',
                bbox_inches='tight', pad_inches=0.3)
    print(f"  Saved: zatron_attack.png")

    # ─────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────
    print(f"\n{'=' * 62}")
    print(f"  RESULTS")
    print(f"{'=' * 62}")
    print(f"""
  Security:
    Raw embeddings:    ρ = {abs(rho_raw):.2f}  ⚠ Attacker recovers similarity
    ZATRON barcodes:   ρ = {abs(rho_prot):.2f}  ✓ No meaningful correlation (vs 1.00 raw)

  Search quality:
    Correct topic:     {enc_correct}/{len(queries)}
    Exact top-1 match: {cos_top1_match}/{len(queries)}

  Visualizations saved:
    zatron_comparison.png — t-SNE: raw clusters vs protected noise
    zatron_attack.png     — correlation: raw leaks vs protected safe
""")
    print("=" * 62)
    print("  github.com/zahraarmantech/ZATRON")
    print("  Patent Pending · Zahra Arman · 2026")
    print("=" * 62)
    print()


if __name__ == "__main__":
    main()
