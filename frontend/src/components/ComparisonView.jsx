import React, { useState } from 'react';
import { GitCompare, ArrowRight, TrendingUp, TrendingDown, Minus, Leaf, Award } from 'lucide-react';

export default function ComparisonView({ comparisons, preferences }) {
  const [selectedConfig, setSelectedConfig] = useState('C5_full');

  if (!comparisons || Object.keys(comparisons).length === 0) {
    return (
      <div className="glass-panel" style={{ padding: 40, textAlign: 'center' }}>
        <GitCompare size={36} color="var(--emerald-400)" style={{ margin: '0 auto 16px' }} />
        <h3>No Comparison Data Loaded Yet</h3>
        <p style={{ color: 'var(--text-secondary)', marginTop: 8 }}>
          Configure your preferences and click "Compare Configurations" to view side-by-side rankings.
        </p>
      </div>
    );
  }

  const baselineList = comparisons['C1_baseline'] || [];
  const activeList = comparisons[selectedConfig] || [];

  // Map baseline ranks for fast diff lookup
  const baselineRankMap = {};
  baselineList.forEach((r, idx) => {
    baselineRankMap[r.attraction.id] = idx + 1;
  });

  const configMeta = {
    'C1_baseline': { name: 'C1: Baseline (Interests Only)', desc: 'Pure preference ranking with zero sustainability awareness' },
    'C2_pref_emissions': { name: 'C2: Preferences + Emissions', desc: 'Adds transport distance & modal carbon footprint penalty' },
    'C3_pref_emis_pop': { name: 'C3: + Popularity Balancing', desc: 'Balances high overtourism hotspots towards moderate-visitor gems' },
    'C4_pref_emis_pop_seas': { name: 'C4: + Seasonal Demand', desc: 'Inverts seasonal congestion to prioritize off-peak / shoulder visits' },
    'C5_full': { name: 'C5: Full Multi-Criteria System', desc: 'Complete integrated sustainability index with feasibility constraints' },
  };

  // Compute summary stats
  const baselineEmissions = baselineList.reduce((acc, curr) => acc + (curr.estimated_emissions_kg || 0), 0);
  const activeEmissions = activeList.reduce((acc, curr) => acc + (curr.estimated_emissions_kg || 0), 0);
  const emissionSavings = baselineEmissions > 0 ? (baselineEmissions - activeEmissions) : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Overview Banner */}
      <div className="glass-panel" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="badge badge-emerald">Research Ablation Study</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Baseline vs Multi-Criteria</span>
            </div>
            <h2 style={{ fontSize: '1.4rem', marginTop: 4 }}>
              How Sustainability Reshapes Tourist Recommendations
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', maxWidth: 700, marginTop: 4 }}>
              Compare how each sustainability component (emissions, popularity dispersion, seasonal timing) modifies the top-10 recommended attractions compared to traditional preference-only matching.
            </p>
          </div>

          {/* Savings Metric Card */}
          <div style={{
            background: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: 16,
            padding: '12px 20px',
            textAlign: 'right',
          }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>CO₂e Carbon Shift (Top-10)</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--emerald-400)', fontFamily: 'var(--font-heading)' }}>
              {activeEmissions > 0 ? `${activeEmissions.toFixed(1)} kg` : '0 kg'}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--emerald-400)', display: 'flex', alignItems: 'center', gap: 4, justifyContent: 'flex-end' }}>
              <Leaf size={12} />
              <span>Emissions-conscious routing</span>
            </div>
          </div>
        </div>

        {/* Configuration Selector Pills */}
        <div style={{ display: 'flex', gap: 8, marginTop: 20, flexWrap: 'wrap' }}>
          {Object.entries(configMeta).map(([cfgId, info]) => {
            const isSelected = selectedConfig === cfgId;
            return (
              <button
                key={cfgId}
                id={`btn-config-${cfgId}`}
                onClick={() => setSelectedConfig(cfgId)}
                style={{
                  padding: '8px 16px',
                  borderRadius: 10,
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  border: isSelected ? '1px solid var(--emerald-500)' : '1px solid var(--border-subtle)',
                  background: isSelected ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                  color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                  boxShadow: isSelected ? '0 2px 10px rgba(16, 185, 129, 0.2)' : 'none',
                  transition: 'all 0.15s ease',
                }}
              >
                {info.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* Side-by-side columns: C1 Baseline vs Selected Config */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
        gap: 20,
      }}>
        {/* Baseline Column */}
        <div className="glass-panel" style={{ padding: 20 }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 16,
            borderBottom: '1px solid var(--border-subtle)',
            paddingBottom: 10,
          }}>
            <div>
              <h3 style={{ fontSize: '1.1rem', color: 'var(--text-main)' }}>C1: Baseline Recommendations</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Interest category matching only</p>
            </div>
            <span className="badge badge-neutral">Baseline</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {baselineList.map((item, idx) => (
              <div
                key={item.attraction.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 14px',
                  borderRadius: 10,
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontWeight: 800, fontSize: '0.85rem', color: 'var(--text-muted)', width: 22 }}>
                    #{idx + 1}
                  </span>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.88rem', color: '#ffffff' }}>
                      {item.attraction.name}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {item.attraction.city} • {item.attraction.categories?.slice(0, 2).join(', ')}
                    </div>
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--sapphire-400)' }}>
                    {(item.final_score * 100).toFixed(0)}%
                  </div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                    {item.attraction.annual_visitors ? `${(item.attraction.annual_visitors / 100000).toFixed(1)}L visitors` : 'Unrecorded'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Config Column */}
        <div className="glass-panel" style={{ padding: 20 }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 16,
            borderBottom: '1px solid var(--border-subtle)',
            paddingBottom: 10,
          }}>
            <div>
              <h3 style={{ fontSize: '1.1rem', color: 'var(--emerald-400)' }}>
                {configMeta[selectedConfig]?.name}
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {configMeta[selectedConfig]?.desc}
              </p>
            </div>
            <span className="badge badge-emerald">Ablation Run</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {activeList.map((item, idx) => {
              const currentRank = idx + 1;
              const baseRank = baselineRankMap[item.attraction.id];
              let rankDiff = null;
              if (baseRank !== undefined) {
                rankDiff = baseRank - currentRank; // positive = climbed up, negative = dropped
              }

              return (
                <div
                  key={item.attraction.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: 10,
                    background: rankDiff && rankDiff > 0 ? 'rgba(16, 185, 129, 0.05)' : 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontWeight: 800, fontSize: '0.85rem', color: 'var(--emerald-400)', width: 22 }}>
                      #{currentRank}
                    </span>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.88rem', color: '#ffffff' }}>
                        {item.attraction.name}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {item.attraction.city} • {item.estimated_emissions_kg ? `${item.estimated_emissions_kg} kg CO₂e` : 'Local'}
                      </div>
                    </div>
                  </div>

                  {/* Rank Displacement indicator */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    {baseRank === undefined ? (
                      <span className="badge badge-purple" style={{ fontSize: '0.65rem' }}>
                        New Entry ✨
                      </span>
                    ) : rankDiff > 0 ? (
                      <span style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 2,
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        color: 'var(--emerald-400)',
                      }}>
                        <TrendingUp size={13} />
                        +{rankDiff}
                      </span>
                    ) : rankDiff < 0 ? (
                      <span style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 2,
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        color: 'var(--rose-400)',
                      }}>
                        <TrendingDown size={13} />
                        {rankDiff}
                      </span>
                    ) : (
                      <span style={{
                        display: 'flex',
                        alignItems: 'center',
                        fontSize: '0.72rem',
                        color: 'var(--text-muted)',
                      }}>
                        <Minus size={13} />
                        0
                      </span>
                    )}

                    <div style={{ textAlign: 'right', minWidth: 45 }}>
                      <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--emerald-400)' }}>
                        {(item.final_score * 100).toFixed(0)}%
                      </div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                        Score
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
