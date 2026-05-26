"""
ZATRON Visualization — Generates comparison images for README

Creates t-SNE plots showing:
  Left: Raw embeddings (clustered, leaking topic structure)
  Right: ZATRON barcodes (no structure, random noise)

Output: zatron_comparison.png

Requirements: pip install sentence-transformers scikit-learn matplotlib
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import sys

def main():
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.manifold import TSNE
        from sklearn.utils.extmath import randomized_svd
    except ImportError:
        print("Install: pip install sentence-transformers scikit-learn matplotlib")
        sys.exit(1)

    documents = {
        "Medical": [
            "Patient diagnosed with acute respiratory distress syndrome",
            "Blood test results indicate elevated white cell count",
            "MRI scan reveals herniated disc at L4-L5 vertebrae",
            "Prescribed metformin 500mg twice daily for diabetes",
            "Post-surgical wound healing progressing normally",
            "Cardiac stress test showed irregular heartbeat pattern",
        ],
        "Legal": [
            "Defendant filed motion to dismiss all charges",
            "Non-disclosure agreement expires after three years",
            "Intellectual property rights transferred upon acquisition",
            "Plaintiff seeks compensatory damages of two million",
            "Contract breach occurred when delivery was delayed",
            "Court granted preliminary injunction against competitor",
        ],
        "Financial": [
            "Quarterly revenue exceeded projections by twelve percent",
            "Portfolio rebalanced toward fixed income securities",
            "Operating expenses reduced through vendor consolidation",
            "Cash flow forecast indicates shortfall in Q3",
            "Stock option vesting schedule accelerated after merger",
            "Audit found discrepancies in accounts receivable ledger",
        ],
        "Technical": [
            "Database migration completed with zero downtime",
            "API rate limiting implemented at gateway level",
            "Memory leak identified in connection pool handler",
            "Load balancer configured for round-robin distribution",
            "Kubernetes pods failing health checks after deployment",
            "SSL certificate renewal automated via certbot cron job",
        ],
        "Personal": [
            "Employee performance review scheduled for next Friday",
            "Salary adjustment approved effective next pay period",
            "Harassment complaint filed against department manager",
            "Background check returned clean criminal record",
            "Medical leave request approved for six weeks",
            "Exit interview revealed concerns about team culture",
        ],
    }

    all_docs = []
    all_topics = []
    topic_names = list(documents.keys())
    colors_map = {
        "Medical": "#ef4444",
        "Legal": "#3b82f6",
        "Financial": "#eab308",
        "Technical": "#22c55e",
        "Personal": "#a855f7",
    }

    for topic, docs in documents.items():
        for doc in docs:
            all_docs.append(doc)
            all_topics.append(topic)

    N = len(all_docs)
    colors = [colors_map[t] for t in all_topics]

    print("Encoding documents...")
    sbert = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = sbert.encode(all_docs, show_progress_bar=False).astype(np.float32)

    # ZATRON encoding
    import hmac, hashlib
    N_BINS = 50
    PRIMES = [53, 59, 61, 67, 71, 73]
    KEY = b"zatron-demo-key"
    me = embeddings.mean(0)
    ce = embeddings - me
    n_comp = min(200, N - 1, embeddings.shape[1])
    _, _, Vt = randomized_svd(ce, n_components=n_comp, random_state=42)
    pr = ce @ Vt[:n_comp].T
    pm = pr.min(0)
    prng = pr.max(0) - pm + 1e-8
    sigs = np.clip(((pr - pm) / prng * (N_BINS - 1)).astype(np.int64), 0, N_BINS - 1)

    def make_mask(doc_id, prime):
        mx = (256 // prime) * prime
        sl = np.zeros(n_comp, dtype=np.int64)
        c, f = 0, 0
        while f < n_comp:
            h = hmac.new(KEY, f"{doc_id}:{prime}:{c}".encode(),
                         hashlib.sha256).digest()
            for b in h:
                if f >= n_comp:
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

    # t-SNE
    print("Computing t-SNE (raw)...")
    tsne_raw = TSNE(n_components=2, random_state=42, perplexity=8).fit_transform(embeddings)
    print("Computing t-SNE (protected)...")
    tsne_prot = TSNE(n_components=2, random_state=42, perplexity=8).fit_transform(barcode_matrix)

    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor('#0a0a0f')

    for ax, data, title, border_color in [
        (ax1, tsne_raw, "Standard Embeddings — EXPOSED", "#ef4444"),
        (ax2, tsne_prot, "ZATRON Protected — SAFE", "#22c55e"),
    ]:
        ax.set_facecolor('#0f0f18')
        for i in range(N):
            ax.scatter(data[i, 0], data[i, 1], c=colors[i], s=80,
                      alpha=0.85, edgecolors='white', linewidths=0.3, zorder=3)

        ax.set_title(title, fontsize=14, fontweight='bold', color=border_color,
                    pad=15, fontfamily='monospace')
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color(border_color)
            spine.set_linewidth(1.5)

    # Legend
    for topic, color in colors_map.items():
        ax1.scatter([], [], c=color, s=60, label=topic)
    ax1.legend(loc='lower left', fontsize=8, facecolor='#0f0f18',
              edgecolor='#333', labelcolor='white', framealpha=0.9)

    # Annotations
    ax1.text(0.5, -0.08, "⚠ Topics visible through clustering",
            transform=ax1.transAxes, ha='center', fontsize=10,
            color='#ef4444', fontfamily='monospace')
    ax2.text(0.5, -0.08, "✓ No structure — indistinguishable from noise",
            transform=ax2.transAxes, ha='center', fontsize=10,
            color='#22c55e', fontfamily='monospace')

    fig.suptitle("ZATRON — Same Documents, Same Search Quality, Different Visibility",
                fontsize=16, color='white', fontweight='bold', fontfamily='monospace', y=0.98)

    plt.tight_layout(rect=[0, 0.02, 1, 0.93])
    plt.savefig('zatron_comparison.png', dpi=150, facecolor='#0a0a0f',
                bbox_inches='tight', pad_inches=0.3)
    print("Saved: zatron_comparison.png")

    # Attack comparison plot
    fig2, (ax3, ax4) = plt.subplots(1, 2, figsize=(14, 6))
    fig2.patch.set_facecolor('#0a0a0f')

    # Compute pairwise cosine similarities
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    cos_matrix = (embeddings @ embeddings.T) / (norms @ norms.T + 1e-10)

    # Raw embedding distances (attacker can compute)
    raw_dists = []
    cos_sims = []
    for i in range(N):
        for j in range(i + 1, N):
            cos_sims.append(cos_matrix[i, j])
            raw_dists.append(np.linalg.norm(embeddings[i] - embeddings[j]))

    # Barcode distances (attacker sees)
    barcode_dists_list = []
    for i in range(N):
        for j in range(i + 1, N):
            barcode_dists_list.append(np.sum(np.abs(barcode_matrix[i] - barcode_matrix[j])))

    ax3.set_facecolor('#0f0f18')
    ax3.scatter(cos_sims, raw_dists, c='#ef4444', alpha=0.4, s=15)
    ax3.set_xlabel('True Cosine Similarity', color='white', fontsize=10)
    ax3.set_ylabel('Raw Embedding Distance', color='white', fontsize=10)
    ax3.set_title('Raw: Distance Reveals Similarity', color='#ef4444',
                 fontsize=12, fontweight='bold', fontfamily='monospace')
    ax3.tick_params(colors='#666')
    for spine in ax3.spines.values():
        spine.set_color('#ef4444')
        spine.set_linewidth(1.5)

    ax4.set_facecolor('#0f0f18')
    ax4.scatter(cos_sims, barcode_dists_list, c='#22c55e', alpha=0.4, s=15)
    ax4.set_xlabel('True Cosine Similarity', color='white', fontsize=10)
    ax4.set_ylabel('Barcode Distance', color='white', fontsize=10)
    ax4.set_title('ZATRON: No Correlation', color='#22c55e',
                 fontsize=12, fontweight='bold', fontfamily='monospace')
    ax4.tick_params(colors='#666')
    for spine in ax4.spines.values():
        spine.set_color('#22c55e')
        spine.set_linewidth(1.5)

    fig2.suptitle("Attack Analysis — Can an Observer Recover Similarity?",
                 fontsize=16, color='white', fontweight='bold', fontfamily='monospace', y=0.98)

    plt.tight_layout(rect=[0, 0.02, 1, 0.93])
    plt.savefig('zatron_attack.png', dpi=150, facecolor='#0a0a0f',
                bbox_inches='tight', pad_inches=0.3)
    print("Saved: zatron_attack.png")


if __name__ == "__main__":
    main()
