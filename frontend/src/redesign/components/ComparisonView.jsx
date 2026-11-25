import React, { useState } from 'react';
import { 
  GitCompare, ArrowRight, TrendingUp, TrendingDown, Minus, 
  Leaf, Award, Sparkles, Layers 
} from 'lucide-react';

export default function ComparisonView({ comparisons, preferences }) {
  const [selectedConfig, setSelectedConfig] = useState('C5_full');

  if (!comparisons || Object.keys(comparisons).length === 0) {
    return (
      <div className="at-card" style={{ padding: 48, textAlign: 'center' }}>
        <GitCompare size={42} color="var(--c-accent)" style={{ margin: '0 auto 16px' }} />
        <h3 style={{ fontSize: '1.4rem', color: 'var(--c-primary)' }}>No Comparison Data Loaded Yet</h3>
        <p style={{ color: 'var(--c-text-secondary)', marginTop: 8 }}>
          Configure your preferences in the Recommendations Studio to view side-by-side ablation rankings.
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
    'C1_baseline': { 
      name: 'C1: Baseline (Interests Only)', 
      desc: 'Traditional content matching ranking strictly by category affinity, ignoring carbon, crowding, and seasonality.' 
    },
    'C2_pref_emissions': { 
      name: 'C2: Preferences + Transit Carbon', 
      desc: 'Incentivizes low-carbon modal transit (rail & bus) and penalizes long-distance private vehicle legs.' 
    },
    'C3_pref_emis_pop': { 
      name: 'C3: + Popularity Dispersion', 
      desc: 'Reduces overtourism stress by dispersing tourist traffic from congested landmarks to cultural gems.' 
    },
    'C4_pref_emis_pop_seas': { 
      name: 'C4: + Seasonal Demand', 
      desc: 'Adjusts recommendations based on monthly climate comfort and historical regional visitor surges.' 
    },
    'C5_full': { 
      name: 'C5: Full Multi-Criteria System', 
      desc: 'Full composite Pareto-optimal ranking balancing interest matching, transit emissions, and crowd relief.' 
    },
  };

  const baselineEmissions = baselineList.reduce((acc, curr) => acc + (curr.estimated_emissions_kg || 0), 0);
  const activeEmissions = activeList.reduce((acc, curr) => acc + (curr.estimated_emissions_kg || 0), 0);
  const emissionSavings = baselineEmissions > 0 ? (baselineEmissions - activeEmissions) : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      {/* Overview Card */}
      <div className="at-card" style={{ padding: 32 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 20 }}>
          <div>
            <div className="at-page-tagline" style={{ marginBottom: 8 }}>
              <Layers size={14} color="var(--c-accent)" />
              <span>Academic Ablation Study</span>
            </div>
            <h2 style={{ fontSize: '2rem', color: 'var(--c-primary)', marginBottom: 6 }}>
              How Sustainability Transforms Recommendations
            </h2>
            <p style={{ color: 'var(--c-text-secondary)', fontSize: '0.94rem', maxWidth: 740, lineHeight: 1.6 }}>
              Compare how progressively adding modal carbon optimization, crowd dispersion, and climate seasonality 
              restructures the top-10 recommended destinations relative to traditional preference-only matching.
            </p>
          </div>

          {/* Savings Metric Card */}
          <div style={{
            backgroundColor: 'var(--c-bg-subtle)',
            border: '1px solid var(--c-border)',
            borderRadius: 'var(--radius-lg)',
            padding: '18px 24px',
            textAlign: 'right',
            boxShadow: 'var(--shadow-xs)',
          }}>
            <div style={{ fontSize: '0.74rem', color: 'var(--c-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
              Top-10 Transit Footprint
            </div>
            <div style={{
              fontFamily: 'var(--font-serif)',
              fontSize: '2rem',
              color: 'var(--c-primary)',
              margin: '3px 0',
            }}>
              {activeEmissions > 0 ? `${activeEmissions.toFixed(1)} kg` : '0 kg'}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--c-primary)', display: 'flex', alignItems: 'center', gap: 5, justifyContent: 'flex-end', fontWeight: 600 }}>
              <Leaf size={14} color="var(--c-accent)" />
              <span>
                {emissionSavings > 0 ? `-${emissionSavings.toFixed(1)} kg CO₂e vs Baseline` : 'Emissions-Conscious Routing'}
              </span>
            </div>
          </div>
        </div>

        {/* Configuration Selector Pills */}
        <div className="at-config-pill-bar">
          {Object.entries(configMeta).map(([cfgId, info]) => {
            const isSelected = selectedConfig === cfgId;
            return (
              <button
                key={cfgId}
                id={`btn-config-${cfgId}`}
                type="button"
                onClick={() => setSelectedConfig(cfgId)}
                className={`at-config-pill ${isSelected ? 'active' : ''}`}
              >
                {info.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* Side-by-Side Comparison Columns */}
      <div className="at-ablation-columns">
        {/* Baseline Column */}
        <div className="at-card" style={{ padding: 26 }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 18,
            paddingBottom: 14,
            borderBottom: '1px solid var(--c-border-subtle)',
          }}>
            <div>
              <h3 style={{ fontSize: '1.25rem', color: 'var(--c-primary)' }}>
                C1: Baseline Recommendations
              </h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--c-text-muted)' }}>
                Interest category matching only
              </p>
            </div>
            <span className="at-badge at-badge-neutral">Baseline</span>
          </div>

          <div>
            {baselineList.map((item, idx) => (
              <div key={item.attraction.id} className="at-ablation-row">
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{
                    width: 28,
                    height: 28,
                    borderRadius: '50%',
                    background: 'var(--c-border)',
                    color: 'var(--c-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.82rem',
                    fontWeight: 700,
                  }}>
                    #{idx + 1}
                  </span>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.94rem', color: 'var(--c-primary)' }}>
                      {item.attraction.name}
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--c-text-muted)' }}>
                      {item.attraction.city} • {item.attraction.categories?.slice(0, 2).join(', ')}
                    </div>
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--c-accent)' }}>
                    {(item.final_score * 100).toFixed(0)}%
                  </div>
                  <div style={{ fontSize: '0.74rem', color: 'var(--c-text-muted)' }}>
                    {item.attraction.annual_visitors ? `${(item.attraction.annual_visitors / 100000).toFixed(1)}L visitors` : 'Unrecorded'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Config Column */}
        <div className="at-card" style={{ padding: 26, borderTop: '4px solid var(--c-accent)' }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 18,
            paddingBottom: 14,
            borderBottom: '1px solid var(--c-border-subtle)',
          }}>
            <div>
              <h3 style={{ fontSize: '1.25rem', color: 'var(--c-accent)' }}>
                {configMeta[selectedConfig]?.name}
              </h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--c-text-muted)' }}>
                {configMeta[selectedConfig]?.desc}
              </p>
            </div>
            <span className="at-badge at-badge-accent">Ablation Run</span>
          </div>

          <div>
            {activeList.map((item, idx) => {
              const currentRank = idx + 1;
              const baseRank = baselineRankMap[item.attraction.id];
              let rankDiff = null;
              if (baseRank !== undefined) {
                rankDiff = baseRank - currentRank; // positive = climbed up
              }

              return (
                <div
                  key={item.attraction.id}
                  className={`at-ablation-row ${rankDiff && rankDiff > 0 ? 'climbed' : ''}`}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span style={{
                      width: 28,
                      height: 28,
                      borderRadius: '50%',
                      background: 'var(--c-primary)',
                      color: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.82rem',
                      fontWeight: 700,
                    }}>
                      #{currentRank}
                    </span>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.94rem', color: 'var(--c-primary)' }}>
                        {item.attraction.name}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--c-text-muted)' }}>
                        {item.attraction.city} • {item.estimated_emissions_kg ? `${item.estimated_emissions_kg} kg CO₂e` : 'Low transit'}
                      </div>
                    </div>
                  </div>

                  {/* Rank Displacement indicator */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    {baseRank === undefined ? (
                      <span className="at-badge at-badge-accent" style={{ fontSize: '0.7rem' }}>
                        New Entry ✨
                      </span>
                    ) : rankDiff > 0 ? (
                      <span style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 2,
                        fontSize: '0.8rem',
                        fontWeight: 700,
                        color: 'var(--c-primary)',
                      }}>
                        <TrendingUp size={15} />
                        +{rankDiff}
                      </span>
                    ) : rankDiff < 0 ? (
                      <span style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 2,
                        fontSize: '0.8rem',
                        fontWeight: 700,
                        color: 'var(--c-rose)',
                      }}>
                        <TrendingDown size={15} />
                        {rankDiff}
                      </span>
                    ) : (
                      <span style={{
                        display: 'flex',
                        alignItems: 'center',
                        fontSize: '0.8rem',
                        color: 'var(--c-text-muted)',
                      }}>
                        <Minus size={15} />
                        0
                      </span>
                    )}

                    <div style={{ textAlign: 'right', minWidth: 50 }}>
                      <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--c-primary)' }}>
                        {(item.final_score * 100).toFixed(0)}%
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--c-text-muted)' }}>
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
