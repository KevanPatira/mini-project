import React, { useState } from 'react';
import { 
  Plus, Check, MapPin, Clock, Award, Leaf, Sparkles, Navigation, 
  ShieldCheck, Wallet, Layers, ChevronDown, ChevronUp
} from 'lucide-react';
import { getTransportIcon, formatFare, formatDistance, formatDuration } from '../../utils/transport';

export default function RecommendationCard({
  item,
  onAddToItinerary,
  isInItinerary,
  rank,
}) {
  const [showTransitOptions, setShowTransitOptions] = useState(false);
  const { attraction, final_score, score_breakdown, explanation } = item;
  const emissionsKg = item.estimated_emissions_kg;
  const distanceKm = item.distance_km;
  const travelHours = item.travel_hours;
  const transportMode = item.transport_mode;
  const estimatedCostInr = item.estimated_cost_inr;
  const transportSource = item.transport_source;
  const transitOptions = item.transit_options || {};

  const scorePercent = Math.round(final_score * 100);
  const isTopPick = rank <= 3;
  const TransportIcon = getTransportIcon(transportMode);

  return (
    <div
      className="at-discovery-card at-fade-in"
      style={{ position: 'relative', overflow: 'hidden' }}
      onMouseEnter={(e) => {
        const stripe = e.currentTarget.querySelector('.at-card-accent-stripe');
        if (stripe) stripe.style.opacity = '1';
      }}
      onMouseLeave={(e) => {
        const stripe = e.currentTarget.querySelector('.at-card-accent-stripe');
        if (stripe) stripe.style.opacity = '0';
      }}
    >
      {/* Subtle left-side accent stripe on hover */}
      <div
        className="at-card-accent-stripe"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: 4,
          height: '100%',
          background: 'linear-gradient(to bottom, var(--c-primary), var(--c-accent))',
          opacity: 0,
          transition: 'opacity 240ms ease',
          zIndex: 2,
          borderRadius: '4px 0 0 4px',
        }}
      />

      {/* Visual Decorative Cover */}
      <div className="at-card-cover">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className={`at-card-rank-badge ${isTopPick ? 'top-pick' : ''}`}>
            {isTopPick ? `★ Rank #${rank}` : `Rank #${rank}`}
          </span>
          <span className="at-badge at-badge-neutral" style={{ fontSize: '0.72rem' }}>
            {attraction.district} District
          </span>
        </div>

        <div
          className="at-composite-score-badge"
          title="Multi-Criteria Composite Utility Index"
          style={{ transition: 'transform 200ms ease' }}
          onMouseEnter={(e) => { e.currentTarget.style.transform = 'scale(1.08)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.transform = 'scale(1)'; }}
        >
          <Sparkles size={13} color="var(--c-accent)" />
          <span>{scorePercent}% Match</span>
        </div>
      </div>

      {/* Main Card Body */}
      <div className="at-card-content">
        {/* Title and Location */}
        <div>
          <h3 className="at-card-title">{attraction.name}</h3>
          <div className="at-card-location">
            <MapPin size={14} color="var(--c-accent)" />
            <span>{attraction.city}, Rajasthan</span>
          </div>
        </div>

        {/* Heritage Status & Categories */}
        <div className="at-card-tag-row">
          {attraction.heritage_status && (
            <span className="at-badge at-badge-amber">
              <Award size={12} />
              <span>{attraction.heritage_status}</span>
            </span>
          )}
          {attraction.categories?.map((cat) => (
            <span key={cat} className="at-badge at-badge-neutral" style={{ textTransform: 'capitalize' }}>
              {cat}
            </span>
          ))}
          {attraction.visitor_data_source === 'observed' && (
            <span className="at-badge at-badge-sustain">
              <ShieldCheck size={12} />
              <span>Verified ASI Site</span>
            </span>
          )}
        </div>

        {/* Description */}
        <p className="at-card-desc">
          {attraction.description}
        </p>

        {/* Multi-Criteria Balanced Meters */}
        <div className="at-criteria-box">
          <div className="at-criteria-label-row">
            Multi-Criteria Performance Dimensions
          </div>

          <div className="at-criteria-grid">
            {/* Interest Alignment */}
            <div>
              <div className="at-meter-header">
                <span>Interest Match</span>
                <strong style={{ color: 'var(--c-accent)' }}>
                  {(score_breakdown.preference_score * 100).toFixed(0)}%
                </strong>
              </div>
              <div className="at-meter-track">
                <div 
                  className="at-meter-fill" 
                  style={{ width: `${score_breakdown.preference_score * 100}%`, backgroundColor: 'var(--c-accent)' }} 
                />
              </div>
            </div>

            {/* Low Carbon */}
            <div>
              <div className="at-meter-header">
                <span>Low Carbon Transit</span>
                <strong style={{ color: 'var(--c-primary)' }}>
                  {(score_breakdown.emission_score * 100).toFixed(0)}%
                </strong>
              </div>
              <div className="at-meter-track">
                <div 
                  className="at-meter-fill" 
                  style={{ width: `${score_breakdown.emission_score * 100}%`, backgroundColor: 'var(--c-primary)' }} 
                />
              </div>
            </div>

            {/* Crowd Dispersion */}
            <div>
              <div className="at-meter-header">
                <span>Crowd Dispersion</span>
                <strong style={{ color: 'var(--c-secondary)' }}>
                  {(score_breakdown.popularity_score * 100).toFixed(0)}%
                </strong>
              </div>
              <div className="at-meter-track">
                <div 
                  className="at-meter-fill" 
                  style={{ width: `${score_breakdown.popularity_score * 100}%`, backgroundColor: 'var(--c-secondary)' }} 
                />
              </div>
            </div>

            {/* Seasonal Suitability */}
            <div>
              <div className="at-meter-header">
                <span>Seasonal Balance</span>
                <strong style={{ color: 'var(--c-sage-dark)' }}>
                  {(score_breakdown.seasonality_score * 100).toFixed(0)}%
                </strong>
              </div>
              <div className="at-meter-track">
                <div 
                  className="at-meter-fill" 
                  style={{ width: `${score_breakdown.seasonality_score * 100}%`, backgroundColor: 'var(--c-sage)' }} 
                />
              </div>
            </div>
          </div>
        </div>

        {/* Transit Distance, Fare & CO2 Summary */}
        {distanceKm !== undefined && (
          <div style={{
            marginTop: 14,
            backgroundColor: 'var(--c-bg-subtle, #f8f6f0)',
            borderRadius: 'var(--radius-md, 8px)',
            border: '1px solid var(--c-border-subtle, #e5e0d4)',
            padding: '12px 14px',
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 8,
              fontSize: '0.82rem',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 700, color: 'var(--c-primary, #1F3A32)' }}>
                <TransportIcon size={15} color="var(--c-accent, #C56B45)" />
                <span style={{ textTransform: 'capitalize' }}>{transportMode || 'Transit'} Route:</span>
                <span>{Math.round(distanceKm)} km</span>
                {travelHours && <span style={{ color: 'var(--c-text-muted, #7c887e)', fontWeight: 500 }}>• ~{travelHours.toFixed(1)} hrs</span>}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {estimatedCostInr !== undefined && estimatedCostInr !== null && (
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 3,
                    color: 'var(--c-accent, #C56B45)',
                    fontWeight: 700,
                    fontSize: '0.84rem',
                  }}>
                    <Wallet size={13} />
                    ₹{Math.round(estimatedCostInr)}
                  </span>
                )}
                {emissionsKg !== undefined && (
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 3,
                    color: 'var(--c-primary, #1F3A32)',
                    fontWeight: 700,
                    fontSize: '0.82rem',
                  }}>
                    <Leaf size={13} />
                    {emissionsKg} kg CO₂e
                  </span>
                )}
              </div>
            </div>

            {/* Transport Data Source & Alternative Options Toggle */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '0.72rem',
              color: 'var(--c-text-muted, #7c887e)',
              borderTop: '1px dashed var(--c-border-subtle, #e5e0d4)',
              paddingTop: 6,
              flexWrap: 'wrap',
              gap: 6,
            }}>
              <span>
                Source: <strong>{transportSource || 'Empirical Transport Matrix'}</strong>
              </span>

              {Object.keys(transitOptions).length > 1 && (
                <button
                  type="button"
                  onClick={() => setShowTransitOptions(!showTransitOptions)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--c-accent, #C56B45)',
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 3,
                    fontWeight: 600,
                    fontSize: '0.74rem',
                    padding: 0,
                  }}
                >
                  <Layers size={11} />
                  <span>{showTransitOptions ? 'Hide Modes' : 'Compare Modes'}</span>
                  {showTransitOptions ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                </button>
              )}
            </div>

            {/* Expanded Transit Modes Comparison */}
            {showTransitOptions && Object.keys(transitOptions).length > 0 && (
              <div style={{
                marginTop: 4,
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                gap: 6,
                paddingTop: 4,
              }}>
                {Object.entries(transitOptions).map(([modeKey, opt]) => {
                  const ModeIcon = getTransportIcon(modeKey);
                  const isCurrent = modeKey === transportMode;
                  return (
                    <div
                      key={modeKey}
                      style={{
                        padding: '6px 8px',
                        borderRadius: 6,
                        backgroundColor: isCurrent ? 'var(--c-sage-soft, #e6ebe7)' : '#ffffff',
                        border: `1px solid ${isCurrent ? 'var(--c-primary, #1F3A32)' : 'var(--c-border-subtle, #e5e0d4)'}`,
                        fontSize: '0.72rem',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontWeight: 700, textTransform: 'capitalize', color: 'var(--c-primary, #1F3A32)' }}>
                        <ModeIcon size={12} color="var(--c-accent, #C56B45)" />
                        <span>{modeKey}</span>
                        {isCurrent && <span style={{ fontSize: '0.65rem', color: 'var(--c-accent, #C56B45)' }}>(Picked)</span>}
                      </div>
                      <div style={{ color: 'var(--c-text-secondary, #59665c)', marginTop: 2 }}>
                        {opt.estimated_cost_inr ? `₹${Math.round(opt.estimated_cost_inr)}` : 'N/A'} • {opt.travel_hours}h
                      </div>
                      <div style={{ color: 'var(--c-primary, #1F3A32)', fontWeight: 600 }}>
                        {opt.emissions_kg} kg CO₂e
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Editorial Why Note */}
        <div className="at-editorial-quote">
          <strong>Curator's Note:</strong> {explanation}
        </div>
      </div>

      {/* Card Action Footer */}
      <div className="at-card-bottom-actions" style={{ padding: '16px 24px', backgroundColor: 'var(--c-bg-page)' }}>
        <div style={{ fontSize: '0.8rem', color: 'var(--c-text-muted)' }}>
          {attraction.estimated_visit_duration_hours ? `Duration: ${attraction.estimated_visit_duration_hours}h` : 'Full-day site'}
          {attraction.entry_fee ? ` • Fee: ${attraction.entry_fee.split(',')[0]}` : ''}
        </div>

        <button
          id={`btn-add-itinerary-${attraction.id}`}
          type="button"
          onClick={() => onAddToItinerary(attraction.id)}
          className={isInItinerary ? 'at-btn-secondary' : 'at-btn-primary'}
          style={{
            padding: '8px 18px',
            fontSize: '0.84rem',
            ...(isInItinerary ? {
              backgroundColor: 'var(--c-sage-soft)',
              borderColor: 'var(--c-primary)',
              color: 'var(--c-primary)',
              fontWeight: 700,
            } : {})
          }}
        >
          {isInItinerary ? (
            <>
              <Check size={15} />
              <span>In Itinerary</span>
            </>
          ) : (
            <>
              <Plus size={15} />
              <span>Add to Route</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
