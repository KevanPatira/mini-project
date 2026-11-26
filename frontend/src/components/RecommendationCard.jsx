import React, { useState } from 'react';
import { 
  Plus, Check, MapPin, Clock, Award, Info, Leaf, Sparkles, Navigation,
  Wallet, Layers, ChevronDown, ChevronUp
} from 'lucide-react';
import { getTransportIcon } from '../utils/transport';

export default function RecommendationCard({
  item,
  onAddToItinerary,
  isInItinerary,
  rank,
}) {
  const [showTransitOptions, setShowTransitOptions] = useState(false);
  const { attraction, final_score, score_breakdown, explanation, data_quality_notes } = item;
  const emissionsKg = item.estimated_emissions_kg;
  const distanceKm = item.distance_km;
  const travelHours = item.travel_hours;
  const transportMode = item.transport_mode;
  const estimatedCostInr = item.estimated_cost_inr;
  const transportSource = item.transport_source;
  const transitOptions = item.transit_options || {};

  const scorePercent = Math.round(final_score * 100);
  const TransportIcon = getTransportIcon(transportMode);

  // Score color
  const getScoreColor = (score) => {
    if (score >= 0.75) return 'var(--emerald-400)';
    if (score >= 0.5) return 'var(--sapphire-400)';
    return 'var(--amber-400)';
  };

  return (
    <div className="glass-panel" style={{
      padding: '20px',
      position: 'relative',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
    }}>
      {/* Top Bar with Rank and Badges */}
      <div>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: 12,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 32,
              height: 32,
              borderRadius: '50%',
              background: rank <= 3 ? 'linear-gradient(135deg, var(--emerald-500), #047857)' : 'rgba(255, 255, 255, 0.08)',
              color: '#ffffff',
              fontWeight: 800,
              fontSize: '0.9rem',
              boxShadow: rank <= 3 ? '0 0 12px var(--emerald-glow)' : 'none',
            }}>
              #{rank}
            </span>
            <div>
              <h4 style={{ fontSize: '1.15rem', color: '#ffffff', marginBottom: 2 }}>
                {attraction.name}
              </h4>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                <MapPin size={13} color="var(--sapphire-400)" />
                <span>{attraction.city}, {attraction.district} District</span>
              </div>
            </div>
          </div>

          {/* Composite Score Pill */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
          }}>
            <div style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: `1px solid ${getScoreColor(final_score)}`,
              padding: '4px 10px',
              borderRadius: 12,
              display: 'flex',
              alignItems: 'center',
              gap: 5,
            }}>
              <Sparkles size={13} color={getScoreColor(final_score)} />
              <span style={{
                fontFamily: 'var(--font-heading)',
                fontWeight: 700,
                fontSize: '0.95rem',
                color: getScoreColor(final_score),
              }}>
                {scorePercent}%
              </span>
            </div>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 2 }}>
              Composite Index
            </span>
          </div>
        </div>

        {/* Heritage Status & Categories */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
          {attraction.heritage_status && (
            <span className="badge badge-amber" style={{ fontSize: '0.7rem' }}>
              <Award size={11} />
              {attraction.heritage_status}
            </span>
          )}
          {attraction.categories?.map((cat) => (
            <span key={cat} className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>
              {cat}
            </span>
          ))}
          {attraction.visitor_data_source === 'observed' && (
            <span className="badge badge-emerald" style={{ fontSize: '0.68rem' }}>
              Verified Visitor Data
            </span>
          )}
        </div>

        {/* Description */}
        <p style={{
          fontSize: '0.86rem',
          color: 'var(--text-secondary)',
          lineHeight: 1.5,
          marginBottom: 16,
        }}>
          {attraction.description}
        </p>

        {/* Multi-Criteria Score Breakdown Bars */}
        <div style={{
          background: 'rgba(11, 15, 23, 0.5)',
          borderRadius: 12,
          padding: '12px',
          marginBottom: 14,
          border: '1px solid var(--border-subtle)',
        }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Criteria Performance Breakdown
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px 16px' }}>
            {/* Preference Match */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: 3 }}>
                <span style={{ color: 'var(--text-secondary)' }}>Interest Match</span>
                <span style={{ fontWeight: 600, color: 'var(--sapphire-400)' }}>
                  {(score_breakdown.preference_score * 100).toFixed(0)}%
                </span>
              </div>
              <div style={{ height: 4, background: 'rgba(255, 255, 255, 0.08)', borderRadius: 2, overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${score_breakdown.preference_score * 100}%`,
                  background: 'var(--sapphire-400)',
                  borderRadius: 2,
                }} />
              </div>
            </div>

            {/* Emission Score */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: 3 }}>
                <span style={{ color: 'var(--text-secondary)' }}>Low Carbon</span>
                <span style={{ fontWeight: 600, color: 'var(--emerald-400)' }}>
                  {(score_breakdown.emission_score * 100).toFixed(0)}%
                </span>
              </div>
              <div style={{ height: 4, background: 'rgba(255, 255, 255, 0.08)', borderRadius: 2, overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${score_breakdown.emission_score * 100}%`,
                  background: 'var(--emerald-400)',
                  borderRadius: 2,
                }} />
              </div>
            </div>

            {/* Popularity / Crowd Dispersion */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: 3 }}>
                <span style={{ color: 'var(--text-secondary)' }}>Crowd Dispersion</span>
                <span style={{ fontWeight: 600, color: 'var(--amber-400)' }}>
                  {(score_breakdown.popularity_score * 100).toFixed(0)}%
                </span>
              </div>
              <div style={{ height: 4, background: 'rgba(255, 255, 255, 0.08)', borderRadius: 2, overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${score_breakdown.popularity_score * 100}%`,
                  background: 'var(--amber-400)',
                  borderRadius: 2,
                }} />
              </div>
            </div>

            {/* Seasonal Timing */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: 3 }}>
                <span style={{ color: 'var(--text-secondary)' }}>Seasonal Balance</span>
                <span style={{ fontWeight: 600, color: 'var(--violet-400)' }}>
                  {(score_breakdown.seasonality_score * 100).toFixed(0)}%
                </span>
              </div>
              <div style={{ height: 4, background: 'rgba(255, 255, 255, 0.08)', borderRadius: 2, overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${score_breakdown.seasonality_score * 100}%`,
                  background: 'var(--violet-400)',
                  borderRadius: 2,
                }} />
              </div>
            </div>
          </div>
        </div>

        {/* Transit stats & Fare Summary */}
        {distanceKm && (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
            fontSize: '0.78rem',
            color: 'var(--text-secondary)',
            marginBottom: 12,
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-subtle)',
            padding: '10px 12px',
            borderRadius: 8,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 6 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600, color: 'var(--text-main)' }}>
                <TransportIcon size={14} color="var(--emerald-400)" />
                <span style={{ textTransform: 'capitalize' }}>{transportMode || 'Transit'}:</span>
                <span>{Math.round(distanceKm)} km</span>
                {travelHours && <span style={{ color: 'var(--text-muted)' }}>• ~{travelHours.toFixed(1)} hrs</span>}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {estimatedCostInr !== undefined && estimatedCostInr !== null && (
                  <span style={{ color: 'var(--amber-400)', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 3 }}>
                    <Wallet size={12} />
                    ₹{Math.round(estimatedCostInr)}
                  </span>
                )}
                {emissionsKg !== undefined && (
                  <span style={{ color: 'var(--emerald-400)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 3 }}>
                    <Leaf size={12} />
                    {emissionsKg} kg CO₂e
                  </span>
                )}
              </div>
            </div>

            {/* Source Attribution & Comparison Toggle */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '0.7rem',
              color: 'var(--text-muted)',
              borderTop: '1px dashed var(--border-subtle)',
              paddingTop: 5,
              flexWrap: 'wrap',
              gap: 4,
            }}>
              <span>Source: <b>{transportSource || 'Empirical Transport Matrix'}</b></span>
              {Object.keys(transitOptions).length > 1 && (
                <button
                  type="button"
                  onClick={() => setShowTransitOptions(!showTransitOptions)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--sapphire-400)',
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 3,
                    fontSize: '0.72rem',
                    padding: 0,
                  }}
                >
                  <Layers size={11} />
                  <span>{showTransitOptions ? 'Hide' : 'Compare Modes'}</span>
                  {showTransitOptions ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                </button>
              )}
            </div>

            {/* Mode Comparison Breakdown */}
            {showTransitOptions && Object.keys(transitOptions).length > 0 && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: 6, paddingTop: 4 }}>
                {Object.entries(transitOptions).map(([mKey, opt]) => {
                  const MIcon = getTransportIcon(mKey);
                  const isCur = mKey === transportMode;
                  return (
                    <div
                      key={mKey}
                      style={{
                        padding: '5px 8px',
                        borderRadius: 6,
                        background: isCur ? 'rgba(16, 185, 129, 0.12)' : 'rgba(255, 255, 255, 0.02)',
                        border: `1px solid ${isCur ? 'var(--emerald-500)' : 'var(--border-subtle)'}`,
                        fontSize: '0.7rem',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontWeight: 600, textTransform: 'capitalize', color: 'var(--text-main)' }}>
                        <MIcon size={12} color="var(--emerald-400)" />
                        <span>{mKey}</span>
                        {isCur && <span style={{ fontSize: '0.62rem', color: 'var(--emerald-400)' }}>(Picked)</span>}
                      </div>
                      <div style={{ color: 'var(--text-secondary)', marginTop: 2 }}>
                        {opt.estimated_cost_inr ? `₹${Math.round(opt.estimated_cost_inr)}` : 'N/A'} • {opt.travel_hours}h
                      </div>
                      <div style={{ color: 'var(--emerald-400)', fontWeight: 600 }}>
                        {opt.emissions_kg} kg CO₂e
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Explanation callout */}
        <div style={{
          fontSize: '0.8rem',
          color: 'var(--text-main)',
          background: 'rgba(16, 185, 129, 0.08)',
          borderLeft: '3px solid var(--emerald-500)',
          padding: '8px 12px',
          borderRadius: '0 8px 8px 0',
          marginBottom: 14,
        }}>
          <span style={{ fontWeight: 600, color: 'var(--emerald-400)', marginRight: 5 }}>Why this POI:</span>
          {explanation}
        </div>
      </div>

      {/* Action Footer */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingTop: 12,
        borderTop: '1px solid var(--border-subtle)',
      }}>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          {attraction.estimated_visit_duration_hours ? `Duration: ${attraction.estimated_visit_duration_hours}h` : 'Full-day site'}
          {attraction.entry_fee ? ` • Fee: ${attraction.entry_fee.split(',')[0]}` : ''}
        </div>

        <button
          id={`btn-add-itinerary-${attraction.id}`}
          type="button"
          onClick={() => onAddToItinerary(attraction.id)}
          className={isInItinerary ? 'btn-secondary' : 'btn-primary'}
          style={{
            padding: '6px 14px',
            fontSize: '0.82rem',
            background: isInItinerary ? 'rgba(16, 185, 129, 0.2)' : undefined,
            color: isInItinerary ? 'var(--emerald-400)' : undefined,
            borderColor: isInItinerary ? 'var(--emerald-500)' : undefined,
          }}
        >
          {isInItinerary ? (
            <>
              <Check size={14} />
              <span>In Itinerary</span>
            </>
          ) : (
            <>
              <Plus size={14} />
              <span>Add to Route</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
