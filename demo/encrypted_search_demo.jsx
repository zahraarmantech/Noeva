import { useState, useEffect, useCallback, useRef } from "react";

// Generate fake but realistic clustered embeddings
const generateDocs = () => {
  const topics = [
    { name: "Medical", color: "#ef4444", cx: 0.25, cy: 0.3 },
    { name: "Legal", color: "#3b82f6", cx: 0.7, cy: 0.25 },
    { name: "Financial", color: "#eab308", cx: 0.5, cy: 0.7 },
    { name: "Technical", color: "#22c55e", cx: 0.2, cy: 0.75 },
    { name: "Personal", color: "#a855f7", cx: 0.8, cy: 0.65 },
  ];
  const docs = [];
  const titles = {
    Medical: ["Patient heart condition report", "Blood test results analysis", "Respiratory therapy notes", "Cancer screening follow-up", "Diabetes management plan", "Surgical pre-op assessment", "MRI scan interpretation", "Pediatric vaccination record"],
    Legal: ["Merger acquisition contract", "Employment termination clause", "Intellectual property filing", "Non-disclosure agreement", "Litigation discovery docs", "Corporate compliance audit", "Patent infringement claim", "Real estate deed transfer"],
    Financial: ["Q3 revenue forecast model", "Investment portfolio review", "Tax liability assessment", "Loan default risk analysis", "Annual budget allocation", "Stock option valuation", "Cash flow projection", "Expense reimbursement log"],
    Technical: ["API endpoint documentation", "Database migration script", "Security vulnerability patch", "Cloud deployment pipeline", "Machine learning model card", "Load balancer configuration", "Microservice architecture", "Error handling protocol"],
    Personal: ["Employee performance review", "Salary negotiation notes", "Medical leave application", "Background check results", "Harassment complaint file", "Promotion recommendation", "Disciplinary action record", "Exit interview summary"],
  };
  topics.forEach((topic, ti) => {
    const tDocs = titles[topic.name];
    tDocs.forEach((title, di) => {
      const angle = Math.random() * Math.PI * 2;
      const radius = 0.06 + Math.random() * 0.08;
      docs.push({
        id: ti * 8 + di,
        title,
        topic: topic.name,
        color: topic.color,
        rawX: topic.cx + Math.cos(angle) * radius,
        rawY: topic.cy + Math.sin(angle) * radius,
        protX: 0.1 + Math.random() * 0.8,
        protY: 0.1 + Math.random() * 0.8,
      });
    });
  });
  return { docs, topics };
};

const { docs: DOCS, topics: TOPICS } = generateDocs();

const queries = [
  { text: "breathing problems respiratory", topic: "Medical" },
  { text: "contract termination clause", topic: "Legal" },
  { text: "quarterly revenue projection", topic: "Financial" },
  { text: "deployment pipeline config", topic: "Technical" },
  { text: "employee complaint record", topic: "Personal" },
];

export default function Demo() {
  const [mode, setMode] = useState("explore");
  const [searchQuery, setSearchQuery] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [showAttack, setShowAttack] = useState(false);
  const [attackStep, setAttackStep] = useState(0);
  const [hoveredDoc, setHoveredDoc] = useState(null);
  const [animPhase, setAnimPhase] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setAnimPhase(p => p + 1), 50);
    return () => clearInterval(t);
  }, []);

  const doSearch = useCallback((q) => {
    setSearchQuery(q);
    setShowAttack(false);
    const results = DOCS.filter(d => d.topic === q.topic).slice(0, 5);
    setSearchResults(results);
    setMode("search");
  }, []);

  const startAttack = useCallback(() => {
    setShowAttack(true);
    setAttackStep(0);
    const steps = [1, 2, 3, 4];
    steps.forEach((s, i) => {
      setTimeout(() => setAttackStep(s), (i + 1) * 1200);
    });
  }, []);

  const reset = useCallback(() => {
    setMode("explore");
    setSearchQuery(null);
    setSearchResults([]);
    setShowAttack(false);
    setAttackStep(0);
  }, []);

  const ScatterPlot = ({ type, width = 360, height = 320 }) => {
    const isRaw = type === "raw";
    const pad = 20;

    return (
      <svg width={width} height={height} style={{ background: "rgba(0,0,0,0.3)", borderRadius: 8, border: `1px solid ${isRaw ? "rgba(239,68,68,0.3)" : "rgba(34,197,94,0.3)"}` }}>
        {/* Grid */}
        {[0.25, 0.5, 0.75].map(v => (
          <g key={v}>
            <line x1={pad} y1={pad + v * (height - 2 * pad)} x2={width - pad} y2={pad + v * (height - 2 * pad)} stroke="rgba(255,255,255,0.05)" />
            <line x1={pad + v * (width - 2 * pad)} y1={pad} x2={pad + v * (width - 2 * pad)} y2={height - pad} stroke="rgba(255,255,255,0.05)" />
          </g>
        ))}

        {/* Cluster circles for raw */}
        {isRaw && mode === "explore" && TOPICS.map((t, i) => (
          <circle key={i} cx={pad + t.cx * (width - 2 * pad)} cy={pad + t.cy * (height - 2 * pad)} r={35} fill="none" stroke={t.color} strokeWidth={1} strokeDasharray="3,3" opacity={0.3} />
        ))}

        {/* Attack visualization */}
        {showAttack && isRaw && attackStep >= 2 && (
          <>
            {TOPICS.map((t, i) => (
              <g key={`attack-${i}`}>
                <circle cx={pad + t.cx * (width - 2 * pad)} cy={pad + t.cy * (height - 2 * pad)} r={40 + Math.sin(animPhase * 0.1 + i) * 5} fill={t.color} opacity={0.08} />
                <text x={pad + t.cx * (width - 2 * pad)} y={pad + t.cy * (height - 2 * pad) - 45} textAnchor="middle" fill={t.color} fontSize={9} fontFamily="monospace" opacity={0.8}>{t.name}</text>
              </g>
            ))}
          </>
        )}

        {/* Docs */}
        {DOCS.map((doc) => {
          const x = pad + (isRaw ? doc.rawX : doc.protX) * (width - 2 * pad);
          const y = pad + (isRaw ? doc.rawY : doc.protY) * (height - 2 * pad);
          const isResult = searchResults.some(r => r.id === doc.id);
          const isHovered = hoveredDoc === doc.id;
          const dotColor = isRaw ? doc.color : `hsl(${(doc.id * 47) % 360}, 30%, 50%)`;
          const r = isResult ? 6 : isHovered ? 5 : 3;

          return (
            <g key={doc.id} onMouseEnter={() => setHoveredDoc(doc.id)} onMouseLeave={() => setHoveredDoc(null)} style={{ cursor: "pointer" }}>
              {isResult && (
                <circle cx={x} cy={y} r={12} fill="none" stroke="#fff" strokeWidth={1.5} opacity={0.8}>
                  <animate attributeName="r" values="8;14;8" dur="2s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.8;0.2;0.8" dur="2s" repeatCount="indefinite" />
                </circle>
              )}
              <circle cx={x} cy={y} r={r} fill={isResult ? "#fff" : dotColor} opacity={isResult ? 1 : 0.7} />
              {isHovered && (
                <g>
                  <rect x={x + 8} y={y - 22} width={Math.min(doc.title.length * 5.5 + 10, 180)} height={20} rx={4} fill="rgba(0,0,0,0.85)" stroke="rgba(255,255,255,0.2)" />
                  <text x={x + 13} y={y - 8} fill="#fff" fontSize={9} fontFamily="monospace">{doc.title.slice(0, 30)}</text>
                </g>
              )}
            </g>
          );
        })}

        {/* Attack overlay for protected */}
        {showAttack && !isRaw && attackStep >= 3 && (
          <g>
            <rect x={width / 2 - 70} y={height / 2 - 20} width={140} height={40} rx={6} fill="rgba(34,197,94,0.15)" stroke="rgba(34,197,94,0.5)" />
            <text x={width / 2} y={height / 2 + 5} textAnchor="middle" fill="#22c55e" fontSize={13} fontWeight="bold" fontFamily="monospace">NO STRUCTURE</text>
          </g>
        )}

        {/* Attack result for raw */}
        {showAttack && isRaw && attackStep >= 4 && (
          <g>
            <rect x={width / 2 - 70} y={height / 2 - 20} width={140} height={40} rx={6} fill="rgba(239,68,68,0.15)" stroke="rgba(239,68,68,0.5)" />
            <text x={width / 2} y={height / 2 + 5} textAnchor="middle" fill="#ef4444" fontSize={13} fontWeight="bold" fontFamily="monospace">FULLY EXPOSED</text>
          </g>
        )}
      </svg>
    );
  };

  return (
    <div style={{ minHeight: "100vh", background: "#0a0a0f", color: "#e2e2e2", fontFamily: "'JetBrains Mono', 'Fira Code', monospace", padding: 0, margin: 0 }}>

      {/* Header */}
      <div style={{ textAlign: "center", padding: "30px 20px 10px" }}>
        <div style={{ fontSize: 11, letterSpacing: 6, color: "#22c55e", marginBottom: 8, textTransform: "uppercase" }}>ZATRON</div>
        <h1 style={{ fontSize: 28, fontWeight: 300, margin: 0, letterSpacing: 2 }}>
          <span style={{ color: "#ef4444" }}>EXPOSED</span>
          <span style={{ color: "#333", margin: "0 16px" }}>vs</span>
          <span style={{ color: "#22c55e" }}>PROTECTED</span>
        </h1>
        <div style={{ fontSize: 11, color: "#555", marginTop: 8 }}>Same documents. Same search quality. Different visibility.</div>
      </div>

      {/* Main split view */}
      <div style={{ display: "flex", justifyContent: "center", gap: 20, padding: "20px", flexWrap: "wrap" }}>

        {/* Left: Raw */}
        <div style={{ flex: "0 0 380px", maxWidth: 400 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#ef4444", boxShadow: "0 0 8px #ef4444" }} />
            <span style={{ fontSize: 12, color: "#ef4444", letterSpacing: 2, textTransform: "uppercase" }}>Standard Vector Search</span>
          </div>
          <ScatterPlot type="raw" />
          <div style={{ fontSize: 10, color: "#666", marginTop: 6 }}>
            {mode === "explore" ? "⚠ Clusters reveal document topics to any observer" : `✓ ${searchResults.length} results found`}
          </div>

          {/* Topic legend */}
          {mode === "explore" && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
              {TOPICS.map(t => (
                <div key={t.name} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 9 }}>
                  <div style={{ width: 6, height: 6, borderRadius: "50%", background: t.color }} />
                  <span style={{ color: t.color }}>{t.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Protected */}
        <div style={{ flex: "0 0 380px", maxWidth: 400 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 8px #22c55e" }} />
            <span style={{ fontSize: 12, color: "#22c55e", letterSpacing: 2, textTransform: "uppercase" }}>ZATRON Protected Search</span>
          </div>
          <ScatterPlot type="protected" />
          <div style={{ fontSize: 10, color: "#666", marginTop: 6 }}>
            {mode === "explore" ? "✓ No structure visible — random noise to observer" : `✓ ${searchResults.length} identical results found`}
          </div>
        </div>
      </div>

      {/* Search bar */}
      <div style={{ textAlign: "center", padding: "10px 20px" }}>
        <div style={{ fontSize: 11, color: "#555", marginBottom: 10, letterSpacing: 1 }}>SEARCH A QUERY — SAME RESULTS, DIFFERENT VISIBILITY</div>
        <div style={{ display: "flex", justifyContent: "center", gap: 8, flexWrap: "wrap" }}>
          {queries.map((q, i) => (
            <button key={i} onClick={() => doSearch(q)} style={{
              padding: "8px 14px", fontSize: 10, fontFamily: "inherit",
              background: searchQuery === q ? "rgba(34,197,94,0.2)" : "rgba(255,255,255,0.05)",
              border: `1px solid ${searchQuery === q ? "#22c55e" : "#333"}`,
              color: searchQuery === q ? "#22c55e" : "#888",
              borderRadius: 4, cursor: "pointer", transition: "all 0.2s",
            }}>
              {q.text}
            </button>
          ))}
        </div>
      </div>

      {/* Search results */}
      {mode === "search" && searchResults.length > 0 && (
        <div style={{ maxWidth: 780, margin: "10px auto", padding: "0 20px" }}>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", justifyContent: "center" }}>
            {searchResults.map((doc, i) => (
              <div key={doc.id} style={{
                padding: "8px 12px", background: "rgba(255,255,255,0.03)",
                border: "1px solid #222", borderRadius: 6, fontSize: 10,
                display: "flex", alignItems: "center", gap: 8,
              }}>
                <span style={{ color: "#22c55e", fontWeight: "bold" }}>#{i + 1}</span>
                <span style={{ color: "#aaa" }}>{doc.title}</span>
              </div>
            ))}
          </div>
          <div style={{ textAlign: "center", marginTop: 12, fontSize: 11, color: "#22c55e" }}>
            ↑ Both sides return identical results — but only the left reveals WHY
          </div>
        </div>
      )}

      {/* Attack mode */}
      <div style={{ textAlign: "center", padding: "20px" }}>
        {!showAttack ? (
          <button onClick={startAttack} style={{
            padding: "10px 24px", fontSize: 11, fontFamily: "inherit",
            background: "rgba(239,68,68,0.1)", border: "1px solid #ef4444",
            color: "#ef4444", borderRadius: 4, cursor: "pointer",
            letterSpacing: 2, textTransform: "uppercase",
          }}>
            ▶ Launch MDS Geometry Attack
          </button>
        ) : (
          <div style={{ maxWidth: 500, margin: "0 auto" }}>
            <div style={{ fontSize: 12, color: "#ef4444", marginBottom: 12, letterSpacing: 2 }}>ATTACK IN PROGRESS</div>
            {[
              { label: "Computing pairwise distances...", done: attackStep >= 1 },
              { label: "Building distance matrix...", done: attackStep >= 2 },
              { label: "MDS reconstruction...", done: attackStep >= 3 },
              { label: "Analyzing recovered geometry...", done: attackStep >= 4 },
            ].map((step, i) => (
              <div key={i} style={{
                display: "flex", alignItems: "center", gap: 10, padding: "4px 0",
                opacity: attackStep >= i ? 1 : 0.3, transition: "opacity 0.5s",
              }}>
                <div style={{
                  width: 16, height: 16, borderRadius: "50%", fontSize: 9,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  background: step.done ? (i === 3 ? "rgba(239,68,68,0.2)" : "rgba(255,255,255,0.1)") : "transparent",
                  border: `1px solid ${step.done ? (i === 3 ? "#ef4444" : "#555") : "#333"}`,
                  color: step.done ? "#fff" : "#555",
                }}>
                  {step.done ? "✓" : ""}
                </div>
                <span style={{ fontSize: 11, color: step.done ? "#ccc" : "#555" }}>{step.label}</span>
              </div>
            ))}

            {attackStep >= 4 && (
              <div style={{ marginTop: 16, padding: 16, background: "rgba(0,0,0,0.4)", borderRadius: 8, border: "1px solid #222" }}>
                <div style={{ display: "flex", justifyContent: "space-around" }}>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 24, fontWeight: "bold", color: "#ef4444" }}>ρ = 0.63</div>
                    <div style={{ fontSize: 9, color: "#ef4444", marginTop: 4 }}>STANDARD VECTORS</div>
                    <div style={{ fontSize: 9, color: "#888" }}>Geometry recovered</div>
                  </div>
                  <div style={{ width: 1, background: "#222" }} />
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 24, fontWeight: "bold", color: "#22c55e" }}>ρ = 0.002</div>
                    <div style={{ fontSize: 9, color: "#22c55e", marginTop: 4 }}>PROTECTED VECTORS</div>
                    <div style={{ fontSize: 9, color: "#888" }}>Indistinguishable from noise</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Stats bar */}
      <div style={{ display: "flex", justifyContent: "center", gap: 30, padding: "20px", flexWrap: "wrap", borderTop: "1px solid #151515" }}>
        {[
          { label: "Search Quality", value: "98.2%", sub: "of cosine baseline" },
          { label: "vs FHE Speed", value: "8×", sub: "faster (5ms vs 39ms)" },
          { label: "Security Tests", value: "8/8", sub: "all passed" },
          { label: "Real Documents", value: "626K", sub: "MSMARCO tested" },
        ].map((stat, i) => (
          <div key={i} style={{ textAlign: "center" }}>
            <div style={{ fontSize: 22, fontWeight: "bold", color: "#22c55e" }}>{stat.value}</div>
            <div style={{ fontSize: 10, color: "#888", marginTop: 2 }}>{stat.label}</div>
            <div style={{ fontSize: 8, color: "#555" }}>{stat.sub}</div>
          </div>
        ))}
      </div>

      {/* Reset */}
      {mode !== "explore" && (
        <div style={{ textAlign: "center", paddingBottom: 20 }}>
          <button onClick={reset} style={{
            padding: "6px 16px", fontSize: 10, fontFamily: "inherit",
            background: "transparent", border: "1px solid #333",
            color: "#555", borderRadius: 4, cursor: "pointer",
          }}>
            Reset
          </button>
        </div>
      )}

      <div style={{ textAlign: "center", padding: "10px 20px 20px", fontSize: 9, color: "#333" }}>
        ZATRON · Patent Pending · Zahra Arman · 2026
      </div>
    </div>
  );
}
